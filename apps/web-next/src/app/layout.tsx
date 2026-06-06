import type { Metadata } from "next";
import { Cormorant_Garamond, IBM_Plex_Sans, Noto_Serif_SC } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

const cormorant = Cormorant_Garamond({
  variable: "--font-cormorant",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const notoSerif = Noto_Serif_SC({
  variable: "--font-noto-serif",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const ibmPlex = IBM_Plex_Sans({
  variable: "--font-ibm-plex",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "论文预检查 · Fudan Paper Check",
  description: "论文结构、格式、一致性与参考文献预检查 · 多轮辅导工作流",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${cormorant.variable} ${notoSerif.variable} ${ibmPlex.variable} antialiased`}
      >
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
