import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(12),
});

export type LoginValues = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    companyName: z.string().min(2).max(120),
    fullName: z.string().min(2).max(120),
    email: z.string().email(),
    password: z.string().min(12),
    confirmPassword: z.string().min(12),
  })
  .refine((value) => value.password === value.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export type RegisterValues = z.infer<typeof registerSchema>;
