import type { ThemeConfig } from 'antd';
import { theme } from 'antd';

const antigravityTheme: ThemeConfig = {
    algorithm: theme.darkAlgorithm,
    token: {
        colorPrimary: '#722ed1', // Purple-ish for "Antigravity" mystery
        colorInfo: '#13c2c2',
        borderRadius: 12,
        wireframe: false,
        fontFamily: 'var(--font-geist-sans)',
    },
    components: {
        Button: {
            controlHeight: 44,
            borderRadius: 22,
            algorithm: true, // Enable algorithm for derivative colors
        },
        Card: {
            colorBgContainer: 'rgba(255, 255, 255, 0.04)', // Glass effect base
            backdropFilter: 'blur(10px)',
            borderRadiusLG: 24,
            borderless: true, // We will handle border with CSS for glass effect
        },
        Input: {
            colorBgContainer: 'rgba(255, 255, 255, 0.04)',
            activeBorderColor: '#722ed1',
            hoverBorderColor: '#9254de',
            controlHeight: 44,
            borderRadius: 12,
        },
        Select: {
            selectorBg: 'rgba(255, 255, 255, 0.04)',
            controlHeight: 44,
            borderRadius: 12,
        }
    },
};

export default antigravityTheme;
