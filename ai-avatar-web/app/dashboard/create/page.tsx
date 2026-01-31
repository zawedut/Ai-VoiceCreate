"use client";
import React, { useState } from 'react';
import { Typography, Input, Radio, Button, Card, Spin, Select, Form, message } from 'antd';
import {
    YoutubeOutlined,
    AudioOutlined,
    UserOutlined,
    ThunderboltFilled,
    CheckCircleOutlined,
    PlayCircleFilled
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { TextArea } = Input;

export default function CreateVideoPage() {
    const [loading, setLoading] = useState(false);
    const [generatedVideo, setGeneratedVideo] = useState<string | null>(null);

    const handleGenerate = (values: any) => {
        setLoading(true);
        setGeneratedVideo(null);

        // Simulate generation delay
        setTimeout(() => {
            setLoading(false);
            setGeneratedVideo("https://assets.mixkit.co/videos/preview/mixkit-futuristic-robot-arm-working-on-a-screen-13835-large.mp4"); // Mock video
            message.success('Video synthesized successfully!');
        }, 3000);
    };

    return (
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4">

            {/* Left Column: Controls */}
            <div className="space-y-6">
                <div>
                    <Title level={2} className="!text-white !mb-1">Create Avatar</Title>
                    <Text className="text-gray-400">Transform any video into a new AI persona.</Text>
                </div>

                <Card className="glass-card !border-white/5 !bg-white/5">
                    <Form layout="vertical" onFinish={handleGenerate} initialValues={{ mode: 'avatar' }}>

                        <Form.Item
                            name="url"
                            label={<span className="text-gray-300 font-medium">Reference Video URL</span>}
                            rules={[{ required: true, message: 'Source video is required' }]}
                        >
                            <Input
                                prefix={<YoutubeOutlined className="text-gray-500" />}
                                placeholder="https://youtube.com/watch?v=..."
                                className="!bg-black/20 !border-white/10 !text-white !h-12"
                            />
                        </Form.Item>

                        <div className="grid grid-cols-2 gap-4">
                            <Form.Item name="mode" label={<span className="text-gray-300 font-medium">Generation Mode</span>}>
                                <Radio.Group className="w-full flex">
                                    <Radio.Button value="avatar" className="flex-1 text-center !bg-black/20 !border-white/10 !text-gray-300 hover:!text-white checked:!bg-purple-600 checked:!text-white !h-10 leading-10">
                                        <UserOutlined /> Avatar
                                    </Radio.Button>
                                    <Radio.Button value="voice" className="flex-1 text-center !bg-black/20 !border-white/10 !text-gray-300 hover:!text-white checked:!bg-purple-600 checked:!text-white !h-10 leading-10">
                                        <AudioOutlined /> Voice Only
                                    </Radio.Button>
                                </Radio.Group>
                            </Form.Item>

                            <Form.Item name="voice_model" label={<span className="text-gray-300 font-medium">Voice Model</span>}>
                                <Select
                                    defaultValue="gemini"
                                    className="!h-10"
                                    options={[
                                        { value: 'gemini', label: 'Gemini Flash (Fast)' },
                                        { value: 'elevenlabs', label: 'ElevenLabs (Premium)' },
                                    ]}
                                />
                            </Form.Item>
                        </div>

                        <Form.Item name="personality" label={<span className="text-gray-300 font-medium">Personality & Style Prompt</span>}>
                            <TextArea
                                rows={4}
                                placeholder="E.g. Make the voice sound sarcastic and witty. Keep the tone professional but energetic."
                                className="!bg-black/20 !border-white/10 !text-white"
                            />
                        </Form.Item>

                        <Button
                            type="primary"
                            htmlType="submit"
                            size="large"
                            block
                            loading={loading}
                            icon={!loading && <ThunderboltFilled />}
                            className="h-14 text-lg font-bold mt-4 shadow-lg shadow-purple-500/30 !bg-gradient-to-r !from-purple-600 !to-blue-600 !border-none hover:!opacity-90 transition-all"
                        >
                            {loading ? 'Synthesizing...' : 'GENERATE VIDEO'}
                        </Button>
                    </Form>
                </Card>
            </div>

            {/* Right Column: Preview */}
            <div className="flex flex-col h-full bg-black/20 rounded-3xl border border-white/5 overflow-hidden relative">
                <div className="absolute top-4 right-4 z-10 px-3 py-1 bg-black/60 backdrop-blur rounded-full text-xs text-gray-400 border border-white/10">
                    Preview Monitor
                </div>

                {loading ? (
                    <div className="flex-grow flex flex-col items-center justify-center p-12 text-center text-gray-500 space-y-4">
                        <Spin size="large" />
                        <p className="animate-pulse">Processing neural frames...</p>
                    </div>
                ) : generatedVideo ? (
                    <div className="flex-grow relative group bg-black">
                        <video
                            src={generatedVideo}
                            className="w-full h-full object-cover"
                            loop
                            autoPlay
                            muted
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                            <Button type="primary" shape="circle" size="large" icon={<PlayCircleFilled />} className="!w-16 !h-16 !text-2xl" />
                        </div>
                        <div className="absolute bottom-0 left-0 w-full p-6 bg-gradient-to-t from-black to-transparent">
                            <div className="flex items-center gap-2 text-green-400">
                                <CheckCircleOutlined /> <span className="font-bold">Generation Complete</span>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="flex-grow flex flex-col items-center justify-center p-12 text-center text-gray-600">
                        <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-4">
                            <YoutubeOutlined className="text-3xl opacity-50" />
                        </div>
                        <p>Enter a URL and click Generate to see the magic happen.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
