import { Suspense } from "react";
import RegisterInner from "./RegisterInner";

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-stone-500">加载中…</div>}>
      <RegisterInner />
    </Suspense>
  );
}
