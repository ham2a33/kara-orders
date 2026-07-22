"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type ReactElement } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { recognizePdf, recognizePhoto, recognizeText, recognizeVoice } from "@/lib/ai";
import { extractErrorMessage } from "@/lib/errors";

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

export default function AiPage(): ReactElement {
  const router = useRouter();
  const [text, setText] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [voiceFile, setVoiceFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const photoRef = useRef<HTMLInputElement | null>(null);
  const voiceRef = useRef<HTMLInputElement | null>(null);
  const pdfRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setText(window.localStorage.getItem(draftStorageKey) ?? "");
  }, []);

  const textMutation = useMutation({
    mutationFn: recognizeText,
    onSuccess: (recognition) => {
      router.push(`/ai/review/${recognition.id}`);
    },
  });

  const photoMutation = useMutation({
    mutationFn: recognizePhoto,
    onSuccess: (recognition) => {
      router.push(`/ai/review/${recognition.id}`);
    },
  });

  const voiceMutation = useMutation({
    mutationFn: recognizeVoice,
    onSuccess: (recognition) => {
      router.push(`/ai/review/${recognition.id}`);
    },
  });

  const pdfMutation = useMutation({
    mutationFn: recognizePdf,
    onSuccess: (recognition) => {
      router.push(`/ai/review/${recognition.id}`);
    },
  });

  const saveDraft = (): void => {
    window.localStorage.setItem(draftStorageKey, text);
    setMessage("Черновик сохранён локально.");
  };

  return (
    <div className="space-y-6">
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
            {textMutation.isError ? (
              <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {extractErrorMessage(textMutation.error)}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-3">
              <Button
                type="button"
                disabled={textMutation.isPending || text.trim().length === 0}
                onClick={() => {
                  setMessage(null);
                  textMutation.mutate(text);
                }}
              >
                {textMutation.isPending ? "Распознаём..." : "Извлечь позиции"}
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
                      ref={photoRef}
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      onChange={(event) => setPhotoFile(event.target.files?.[0] ?? null)}
                    />
                    <Button
                      className="w-full"
                      variant="secondary"
                      type="button"
                      disabled={photoMutation.isPending || photoFile == null}
                      onClick={() => {
                        setMessage(null);
                        photoMutation.mutate(photoFile as File);
                      }}
                    >
                      {photoMutation.isPending ? "Загрузка..." : "Открыть проверку"}
                    </Button>
                  </>
                ) : input.title === "Голос" ? (
                  <>
                    <Input
                      ref={voiceRef}
                      type="file"
                      accept="audio/mpeg,audio/wav,audio/mp4,audio/x-m4a"
                      onChange={(event) => setVoiceFile(event.target.files?.[0] ?? null)}
                    />
                    <Button
                      className="w-full"
                      variant="secondary"
                      type="button"
                      disabled={voiceMutation.isPending || voiceFile == null}
                      onClick={() => {
                        setMessage(null);
                        voiceMutation.mutate(voiceFile as File);
                      }}
                    >
                      {voiceMutation.isPending ? "Загрузка..." : "Открыть проверку"}
                    </Button>
                  </>
                ) : input.title === "PDF" ? (
                  <>
                    <Input
                      ref={pdfRef}
                      type="file"
                      accept="application/pdf"
                      onChange={(event) => setPdfFile(event.target.files?.[0] ?? null)}
                    />
                    <Button
                      className="w-full"
                      variant="secondary"
                      type="button"
                      disabled={pdfMutation.isPending || pdfFile == null}
                      onClick={() => {
                        setMessage(null);
                        pdfMutation.mutate(pdfFile as File);
                      }}
                    >
                      {pdfMutation.isPending ? "Загрузка..." : "Открыть проверку"}
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
