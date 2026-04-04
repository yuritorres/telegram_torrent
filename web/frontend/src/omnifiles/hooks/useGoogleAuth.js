import { useState, useEffect } from 'react';
import { GOOGLE_CONFIG } from '../config/google';

const GAPI_SCRIPT_ID = 'gapi-script';
const GSI_SCRIPT_ID = 'google-one-tap-script';

export function useGoogleAuth() {
    const [token, setToken] = useState(null);
    const [user, setUser] = useState(null);
    const [isInitialized, setIsInitialized] = useState(false);

    useEffect(() => {
        const loadScripts = async () => {
            if (!GOOGLE_CONFIG.CLIENT_ID) {
                console.warn("Google Client ID not setup.");
                return;
            }

            // Load GIS (Identity Services)
            if (!document.getElementById(GSI_SCRIPT_ID)) {
                const script = document.createElement('script');
                script.src = 'https://accounts.google.com/gsi/client';
                script.id = GSI_SCRIPT_ID;
                script.async = true;
                script.defer = true;
                document.body.appendChild(script);
            }
            setIsInitialized(true);
        };
        loadScripts();
    }, []);

    const login = () => {
        return new Promise((resolve, reject) => {
            if (!window.google) return reject("Google scripts not loaded");

            const client = window.google.accounts.oauth2.initTokenClient({
                client_id: GOOGLE_CONFIG.CLIENT_ID,
                scope: GOOGLE_CONFIG.SCOPES,
                callback: (tokenResponse) => {
                    if (tokenResponse && tokenResponse.access_token) {
                        setToken(tokenResponse.access_token);
                        resolve(tokenResponse.access_token);
                    } else {
                        reject("Login failed");
                    }
                },
            });
            client.requestAccessToken();
        });
    };

    const logout = () => {
        if (token) {
            window.google.accounts.oauth2.revoke(token, () => {
                setToken(null);
                setUser(null);
            });
        }
    };

    return { token, user, login, logout, isInitialized };
}
