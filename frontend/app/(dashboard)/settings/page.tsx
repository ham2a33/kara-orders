import { redirect } from "next/navigation";

export default function SettingsRedirect(): null {
  redirect("/dashboard/company/settings");
}
