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
    title: "Photo",
    description: "Handwritten orders, supplier notes, or paper slips.",
    details: "JPG, PNG, WEBP",
  },
  {
    title: "Voice",
    description: "Transcribe a spoken order and extract structured items.",
    details: "MP3, WAV, M4A",
  },
  {
    title: "Text",
    description: "Paste a quick text order from a customer or salesperson.",
    details: "Instant extraction",
  },
  {
    title: "PDF",
    description: "Supplier invoices and quotations uploaded as documents.",
    details: "Production PDF parsing",
  },
];

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
    setMessage("Draft saved locally.");
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>AI Order Recognition</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Create orders from any input</h1>
            <p className="max-w-2xl text-muted-foreground">
              Upload a photo, record voice, paste free text, or import a supplier PDF. The backend extracts
              structured items and the user confirms the final order before creation.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/ai/history">Recognition history</Link>
          </Button>
          <Button asChild>
            <Link href="/orders/new">Manual order</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Text recognition</CardTitle>
            <CardDescription>Paste a customer request and let the backend extract order lines.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="aiText">Order text</Label>
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
                {textMutation.isPending ? "Extracting..." : "Extract items"}
              </Button>
              <Button type="button" variant="outline" onClick={saveDraft} disabled={text.trim().length === 0}>
                Save draft
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
                {input.title === "Photo" ? (
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
                      {photoMutation.isPending ? "Uploading..." : "Open review"}
                    </Button>
                  </>
                ) : input.title === "Voice" ? (
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
                      {voiceMutation.isPending ? "Uploading..." : "Open review"}
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
                      {pdfMutation.isPending ? "Uploading..." : "Open review"}
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
