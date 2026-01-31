"use client";
import Link from "next/link";
import { Button, Typography } from "antd";

const { Title, Paragraph } = Typography;

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-10 bg-black">
      <Title level={1} style={{ color: 'white' }}>Antigravity</Title>
      <Paragraph style={{ color: 'gray', fontSize: '1.2rem' }}>
        AI Video Engine
      </Paragraph>

      {/* Fallback navigation using standard anchors if Link fails, but we'll try Button directly first */}
      <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
        <a href="/dashboard">
          <Button type="primary" size="large">
            Enter Dashboard
          </Button>
        </a>
      </div>
    </div>
  );
}
