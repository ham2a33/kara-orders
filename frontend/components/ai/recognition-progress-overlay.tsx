"use client";

import { useEffect, useState, type ReactElement } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { extractErrorDetails, extractErrorMessage } from "@/lib/errors";

export type RecognitionInputKind = "photo" | "pdf" | "voice" | "text";

type RecognitionProgressOverlayProps = {
  open: boolean;
  inputKind: RecognitionInputKind;
  phase: "running" | "success" | "error";
  error: unknown;
  onRetry: () => void;
  onClose: () => void;
};

const analysisLabel: Record<RecognitionInputKind, string> = {
  photo: "Анализ изображения...",
  pdf: "Анализ PDF...",
  voice: "Расшифровка аудио...",
  text: "Анализ текста...",
};

function stepIcon(done: boolean, active: boolean): string {
  if (done) {
    return "✔";
  }
  if (active) {
    return "⏳";
  }
  return "○";
}

export function RecognitionProgressOverlay({
  open,
  inputKind,
  phase,
  error,
  onRetry,
  onClose,
}: RecognitionProgressOverlayProps): ReactElement | null {
  const [progressStep, setProgressStep] = useState(0);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (!open || phase !== "running") {
      return;
    }
    setProgressStep(0);
    const timers = [
      window.setTimeout(() => setProgressStep(1), 600),
      window.setTimeout(() => setProgressStep(2), 1800),
      window.setTimeout(() => setProgressStep(3), 3200),
    ];
    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [open, phase, inputKind]);

  useEffect(() => {
    if (phase === "success") {
      setProgressStep(4);
    }
  }, [phase]);

  useEffect(() => {
    if (!open) {
      setShowDetails(false);
      setProgressStep(0);
    }
  }, [open]);

  if (!open) {
    return null;
  }

  const steps = [
    { label: inputKind === "text" ? "Текст отправлен" : "Файл загружен", index: 0 },
    { label: analysisLabel[inputKind], index: 1 },
    { label: "Распознавание товаров...", index: 2 },
    { label: "Формирование заказа...", index: 3 },
    { label: "Готово", index: 4 },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm">
      <Card className="w-full max-w-lg shadow-lg">
        <CardHeader>
          <CardTitle>{phase === "error" ? "Распознавание не удалось" : "ИИ обрабатывает заказ"}</CardTitle>
          <CardDescription>
            {phase === "error"
              ? "Мы получили ошибку от сервера и не скрыли её. Исправьте причину и попробуйте снова."
              : "Подождите, пока backend извлечёт позиции и подготовит экран проверки."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {phase === "error" ? (
            <>
              <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {extractErrorMessage(error)}
              </p>
              {showDetails ? (
                <pre className="max-h-48 overflow-auto rounded-2xl border bg-muted/40 p-3 text-xs text-muted-foreground whitespace-pre-wrap">
                  {extractErrorDetails(error)}
                </pre>
              ) : null}
              <div className="flex flex-wrap gap-3">
                <Button type="button" onClick={onRetry}>
                  Попробовать снова
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowDetails((value) => !value)}>
                  {showDetails ? "Скрыть детали" : "Показать детали"}
                </Button>
                <Button type="button" variant="ghost" onClick={onClose}>
                  Закрыть
                </Button>
              </div>
            </>
          ) : (
            <ul className="space-y-2 text-sm">
              {steps.map((step) => {
                const done = progressStep > step.index || (phase === "success" && step.index <= 4);
                const active = phase === "running" && progressStep === step.index;
                return (
                  <li key={step.label} className="flex items-center gap-2">
                    <span aria-hidden>{stepIcon(done, active)}</span>
                    <span className={done ? "text-foreground" : active ? "text-foreground font-medium" : "text-muted-foreground"}>
                      {step.label}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
