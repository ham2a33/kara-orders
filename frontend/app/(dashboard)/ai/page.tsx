"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type ReactElement } from "react";
import { useRouter } from "next/navigation";

import {
  RecognitionProgressOverlay,
  type RecognitionInputKind,
} from "@/components/ai/recognition-progress-overlay";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { recognizePdf, recognizePhoto, recognizeText, recognizeVoice } from "@/lib/ai";
import type { AIRecognition } from "@/types/ai";

const draftStorageKey = "kara_orders_ai_text_draft";

const inputs = [
  {
    title: "Фото",
    description: "Рукописные заказы, бумажные листы и заметки поставщика.",
    details: "JPG, PNG, WEBP",
  },
  {
    title: "Голос",
    description: "Преобразуйте устный заказ в структуру товаров.",
    details: "MP3, WAV, M4A",
  },
  {
    title: "Текст",
    description: "Вставьте быстрый текст от клиента или менеджера.",
    details: "Мгновенное распознавание",
  },
  {
    title: "PDF",
    description: "Счета и коммерческие предложения поставщиков.",
    details: "Продвинутое PDF-распознавание",
  },
] as const;

type FlowState = {
  open: boolean;
  phase: "running" | "success" | "error";
  inputKind: RecognitionInputKind;
  error: unknown;
};

const idleFlow: FlowState = {
  open: false,
  phase: "running",
  inputKind: "text",
  error: null,
};

export default function AiPage(): ReactElement {
  const router = useRouter();
  const [text, setText] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [voiceFile, setVoiceFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [flow, setFlow] = useState<FlowState>(idleFlow);
  const retryRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    setText(window.localStorage.getItem(draftStorageKey) ?? "");
  }, []);

  const finishSuccess = useCallback(
    (recognition: AIRecognition) => {
      if (!recognition?.id) {
        setFlow((current) => ({
          ...current,
          phase: "error",
          error: new Error("Сервер не вернул идентификатор распознавания"),
        }));
        return;
      }
      setFlow((current) => ({ ...current, phase: "success" }));
      window.setTimeout(() => {
        setFlow(idleFlow);
        router.push(`/orders/new?recognitionId=${recognition.id}`);
      }, 450);
    },
    [router],
  );

  const runRecognition = useCallback(
    (inputKind: RecognitionInputKind, task: () => Promise<AIRecognition>) => {
      setMessage(null);
      setFlow({ open: true, phase: "running", inputKind, error: null });
      retryRef.current = () => runRecognition(inputKind, task);

      void task()
        .then(finishSuccess)
        .catch((error: unknown) => {
          setFlow((current) => ({ ...current, phase: "error", error }));
        });
    },
    [finishSuccess],
  );

  const saveDraft = (): void => {
    window.localStorage.setItem(draftStorageKey, text);
    setMessage("Черновик сохранён локально.");
  };

  return (
    <div className="space-y-6">
      <RecognitionProgressOverlay
        open={flow.open}
        inputKind={flow.inputKind}
        phase={flow.phase}
        error={flow.error}
        onRetry={() => retryRef.current?.()}
        onClose={() => setFlow(idleFlow)}
      />

      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>ИИ-распознавание</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Создание заказа из любого входа</h1>
            <p className="max-w-2xl text-muted-foreground">
              Загрузите фото, запишите голос, вставьте текст или импортируйте PDF. Backend сам извлечёт позиции, а вы только подтвердите итог.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/ai/history">История распознаваний</Link>
          </Button>
          <Button asChild>
            <Link href="/orders/new">Ручной заказ</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Распознавание текста</CardTitle>
            <CardDescription>Вставьте запрос клиента и передайте структуру заказа в backend.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="aiText">Текст заказа</Label>
              <textarea
                id="aiText"
                rows={6}
                value={text}
                onChange={(event) => setText(event.target.value)}
                className="w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
                placeholder={"Pipe 20 15\nValve 2\nCable 10m 3"}
              />
            </div>
            {message ? (
              <p className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300">
                {message}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-3">
              <Button
                type="button"
                disabled={flow.open && flow.phase === "running" || text.trim().length === 0}
                onClick={() => runRecognition("text", () => recognizeText(text.trim()))}
              >
                Извлечь позиции
              </Button>
              <Button type="button" variant="outline" onClick={saveDraft} disabled={text.trim().length === 0}>
                Сохранить черновик
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          {inputs.map((input) => (
            <Card key={input.title}>
              <CardHeader>
                <CardTitle className="text-xl">{input.title}</CardTitle>
                <CardDescription>{input.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">{input.details}</p>
                {input.title === "Фото" ? (
                  <>
                    <Input
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      onChange={(event) => setPhotoFile(event.target.files?.[0] ?? null)}
                    />
                    {photoFile ? (
                      <p className="text-xs text-muted-foreground">Выбрано: {photoFile.name}</p>
                    ) : null}
                    <Button
                      className="w-full"
                      variant="secondary"
                      type="button"
                      disabled={(flow.open && flow.phase === "running") || photoFile == null}
                      onClick={() => {
                        if (!photoFile) {
                          return;
                        }
                        runRecognition("photo", () => recognizePhoto(photoFile));
                      }}
                    >
                      Открыть проверку
                    </Button>
                  </>
                ) : input.title === "Голос" ? (
                  <>
                    <Input
                      type="file"
                      accept="audio/mpeg,audio/wav,audio/mp4,audio/x-m4a"
                      onChange={(event) => setVoiceFile(event.target.files?.[0] ?? null)}
                    />
                    {voiceFile ? (
                      <p className="text-xs text-muted-foreground">Выбрано: {voiceFile.name}</p>
                    ) : null}
                    <Button
                      className="w-full"
                      variant="secondary"
                      type="button"
                      disabled={(flow.open && flow.phase === "running") || voiceFile == null}
                      onClick={() => {
                        if (!voiceFile) {
                          return;
                        }
                        runRecognition("voice", () => recognizeVoice(voiceFile));
                      }}
                    >
                      Открыть проверку
                    </Button>
                  </>
                ) : input.title === "PDF" ? (
                  <>
                    <Input
                      type="file"
                      accept="application/pdf"
                      onChange={(event) => setPdfFile(event.target.files?.[0] ?? null)}
                    />
                    {pdfFile ? (
                      <p className="text-xs text-muted-foreground">Выбрано: {pdfFile.name}</p>
                    ) : null}
                    <Button
                      className="w-full"
                      variant="secondary"
                      type="button"
                      disabled={(flow.open && flow.phase === "running") || pdfFile == null}
                      onClick={() => {
                        if (!pdfFile) {
                          return;
                        }
                        runRecognition("pdf", () => recognizePdf(pdfFile));
                      }}
                    >
                      Открыть проверку
                    </Button>
                  </>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
