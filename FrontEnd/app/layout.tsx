import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '오키더키',
  description: '오키더키 - 회원가입 및 로그인',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
