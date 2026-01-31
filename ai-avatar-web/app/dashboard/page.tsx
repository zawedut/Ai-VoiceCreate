"use client";
import React, { useState, useEffect } from 'react';
import { Typography, Card, Button, Input, List, Tag, Modal, Form, Empty, message } from 'antd';
import { PlusOutlined, KeyOutlined, DeleteOutlined, RobotOutlined, CheckCircleFilled } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

interface ApiKey {
    id: string;
    provider: string;
    name: string;
    key: string;
    isActive: boolean;
    createdAt: number;
}

export default function DashboardPage() {
    const [keys, setKeys] = useState<ApiKey[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [form] = Form.useForm();

    // Load from LocalStorage
    useEffect(() => {
        const saved = localStorage.getItem('antigravity_api_keys');
        if (saved) {
            setKeys(JSON.parse(saved));
        }
    }, []);

    // Save to LocalStorage
    const saveKeys = (newKeys: ApiKey[]) => {
        setKeys(newKeys);
        localStorage.setItem('antigravity_api_keys', JSON.stringify(newKeys));
    };

    const handleAdd = (values: any) => {
        const newKey: ApiKey = {
            id: Date.now().toString(),
            provider: values.provider,
            name: values.name,
            key: values.key,
            isActive: keys.length === 0, // First one active by default
            createdAt: Date.now(),
        };
        saveKeys([...keys, newKey]);
        setIsModalOpen(false);
        form.resetFields();
        message.success('Neural link established (Key Added)');
    };

    const handleDelete = (id: string) => {
        saveKeys(keys.filter(k => k.id !== id));
        message.info('Neural link severed');
    };

    const toggleActive = (id: string) => {
        const newKeys = keys.map(k => ({
            ...k,
            isActive: k.id === id ? true : false // Only one active per session logic for now
        }));
        saveKeys(newKeys);
        message.success('Active core switched');
    };

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4">

            <div className="flex justify-between items-end">
                <div>
                    <Title level={2} className="!text-white !mb-1">The Brain</Title>
                    <Text className="text-gray-400">Manage your neural connections (API Keys) for generation.</Text>
                </div>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    size="large"
                    onClick={() => setIsModalOpen(true)}
                    className="shadow-lg shadow-purple-500/20"
                >
                    Add Connection
                </Button>
            </div>

            {keys.length === 0 ? (
                <div className="glass-panel rounded-3xl p-12 text-center border-dashed border-2 border-white/10">
                    <Empty
                        image={<RobotOutlined className="text-6xl text-gray-600" />}
                        description={<span className="text-gray-400">No active neural links found. Add an API key to start.</span>}
                    >
                        <Button type="primary" onClick={() => setIsModalOpen(true)}>Initialize Brain</Button>
                    </Empty>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {keys.map(key => (
                        <Card key={key.id} className={`glass-card ${key.isActive ? 'border-purple-500/50 bg-purple-500/5' : ''}`}>
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${key.isActive ? 'bg-purple-500 text-white' : 'bg-white/10 text-gray-400'}`}>
                                        <KeyOutlined />
                                    </div>
                                    <div>
                                        <Text className="block text-white font-medium text-lg">{key.name}</Text>
                                        <Tag color={key.provider === 'OpenAI' ? 'green' : 'blue'} className="border-none bg-white/10 text-xs">
                                            {key.provider}
                                        </Tag>
                                    </div>
                                </div>
                                {key.isActive && <CheckCircleFilled className="text-purple-400 text-xl" />}
                            </div>

                            <div className="bg-black/20 p-3 rounded-lg mb-4 font-mono text-xs text-gray-500 truncate">
                                {key.key.substring(0, 8)}****************{key.key.substring(key.key.length - 4)}
                            </div>

                            <div className="flex gap-2 justify-end">
                                {!key.isActive && (
                                    <Button size="small" type="text" className="text-gray-400 hover:text-white" onClick={() => toggleActive(key.id)}>
                                        Set Active
                                    </Button>
                                )}
                                <Button size="small" type="text" danger icon={<DeleteOutlined />} onClick={() => handleDelete(key.id)} />
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            {/* Add Key Modal */}
            <Modal
                title={<span className="text-white">New Neural Connection</span>}
                open={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                footer={null}
                className="glass-modal" // Need to ensure modal styles sit well on dark mode
            >
                <Form form={form} layout="vertical" onFinish={handleAdd}>
                    <Form.Item name="provider" label={<span className="text-gray-400">Provider</span>} initialValue="OpenAI">
                        <Input className="!bg-white/5 !border-white/10 !text-white" />
                    </Form.Item>
                    <Form.Item name="name" label={<span className="text-gray-400">Label (e.g. My Personal Key)</span>} rules={[{ required: true }]}>
                        <Input placeholder="Enter a name..." className="!bg-white/5 !border-white/10 !text-white" />
                    </Form.Item>
                    <Form.Item name="key" label={<span className="text-gray-400">API Key</span>} rules={[{ required: true }]}>
                        <Input.Password placeholder="sk-..." className="!bg-white/5 !border-white/10 !text-white" />
                    </Form.Item>
                    <div className="flex justify-end gap-2 mt-6">
                        <Button onClick={() => setIsModalOpen(false)} className="!text-white !border-white/20 hover:!bg-white/10">Cancel</Button>
                        <Button type="primary" htmlType="submit">Connect</Button>
                    </div>
                </Form>
            </Modal>
        </div>
    );
}
