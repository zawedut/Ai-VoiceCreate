"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Layout, Menu, Button, Avatar, Typography } from 'antd';
import {
    ThunderboltOutlined,
    SettingOutlined,
    VideoCameraOutlined,
    UserOutlined,
    LogoutOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined
} from '@ant-design/icons';

const { Sider, Content } = Layout;
const { Title } = Typography;

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [collapsed, setCollapsed] = useState(false);
    const pathname = usePathname();

    return (
        <Layout className="min-h-screen bg-transparent">
            {/* Glass Sidebar */}
            <Sider
                trigger={null}
                collapsible
                collapsed={collapsed}
                className="!bg-[#050505]/80 backdrop-blur-xl border-r border-white/10"
                width={260}
            >
                <div className="flex flex-col h-full relative z-10">
                    <div className={`p-6 flex items-center gap-3 decoration-none ${collapsed ? 'justify-center' : ''}`}>
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-500 to-cyan-400 flex items-center justify-center shrink-0">
                            <ThunderboltOutlined className="text-white text-lg" />
                        </div>
                        {!collapsed && (
                            <span className="font-bold text-lg tracking-tight text-white animate-in fade-in duration-300">
                                Antigravity
                            </span>
                        )}
                    </div>

                    <Menu
                        mode="inline"
                        selectedKeys={[pathname]}
                        className="!bg-transparent !border-none px-2 space-y-1 flex-grow"
                        items={[
                            {
                                key: '/dashboard',
                                icon: <SettingOutlined />,
                                label: <Link href="/dashboard">The Brain (APIs)</Link>,
                            },
                            {
                                key: '/dashboard/create',
                                icon: <VideoCameraOutlined />,
                                label: <Link href="/dashboard/create">Create Video</Link>,
                            },
                        ]}
                    />

                    {/* User Profile / Logout */}
                    <div className="p-4 border-t border-white/5 mx-2 mb-2">
                        <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
                            <Avatar icon={<UserOutlined />} className="bg-white/10" />
                            {!collapsed && (
                                <div className="flex flex-col overflow-hidden">
                                    <span className="text-sm font-medium text-white truncate">Admin User</span>
                                    <span className="text-xs text-gray-500 truncate">Pro Plan</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </Sider>

            <Layout className="!bg-transparent relative">
                {/* Background Decoration */}
                <div className="absolute top-0 left-0 w-full h-full pointer-events-none z-0 overflow-hidden">
                    <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] rounded-full bg-purple-600/10 blur-[100px]" />
                </div>

                {/* Header */}
                <header className="h-16 px-6 flex items-center justify-between z-10">
                    <Button
                        type="text"
                        icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                        onClick={() => setCollapsed(!collapsed)}
                        className="!text-gray-400 hover:!text-white"
                    />
                </header>

                {/* Content */}
                <Content className="p-6 md:p-8 z-10 overflow-y-auto">
                    {children}
                </Content>
            </Layout>
        </Layout>
    );
}
