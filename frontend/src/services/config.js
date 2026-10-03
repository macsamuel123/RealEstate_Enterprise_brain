/**
 * Configuration loader
 */

export async function loadConfig(path = '/src/config/config.json') {
    try {
        const response = await fetch(path);
        if (!response.ok) {
            throw new Error(`Failed to load config: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error loading config:', error);
        throw error;
    }
}

export function mergeConfigs(base, override) {
    return {
        ...base,
        ...override,
        theme: { ...base.theme, ...override.theme },
        widgets: { ...base.widgets, ...override.widgets },
        layout: override.layout || base.layout,
    };
}
