import {
    CognitoIdentityProviderClient,
    SignUpCommand,
    InitiateAuthCommand,
    ConfirmSignUpCommand,
    GlobalSignOutCommand
} from "@aws-sdk/client-cognito-identity-provider";

const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const region = import.meta.env.VITE_AWS_REGION || (userPoolId ? userPoolId.split('_')[0] : 'us-east-1');

const config = {
    region,
    userPoolId,
    clientId: import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID,
};

const client = new CognitoIdentityProviderClient({ region: config.region });

export const AuthService = {
    async signUp(email, password) {
        const command = new SignUpCommand({
            ClientId: config.clientId,
            Username: email,
            Password: password,
            UserAttributes: [{ Name: "email", Value: email }],
        });
        return await client.send(command);
    },

    async confirmSignUp(email, code) {
        const command = new ConfirmSignUpCommand({
            ClientId: config.clientId,
            Username: email,
            ConfirmationCode: code,
        });
        return await client.send(command);
    },

    async signIn(email, password) {
        const command = new InitiateAuthCommand({
            AuthFlow: "USER_PASSWORD_AUTH",
            ClientId: config.clientId,
            AuthParameters: {
                USERNAME: email,
                PASSWORD: password,
            },
        });

        const response = await client.send(command);

        if (response.AuthenticationResult) {
            const { AccessToken, IdToken, RefreshToken } = response.AuthenticationResult;
            localStorage.setItem('accessToken', AccessToken);
            localStorage.setItem('idToken', IdToken);
            if (RefreshToken) {
                localStorage.setItem('refreshToken', RefreshToken);
            }
            return { isSignedIn: true };
        }

        return { isSignedIn: false, nextStep: response.ChallengeName };
    },

    async signOut() {
        try {
            const accessToken = localStorage.getItem('accessToken');
            if (accessToken) {
                const command = new GlobalSignOutCommand({
                    AccessToken: accessToken,
                });
                await client.send(command);
            }
        } catch (error) {
            console.error("Error signing out:", error);
        } finally {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('idToken');
            localStorage.removeItem('refreshToken');

            let domain = import.meta.env.VITE_COGNITO_DOMAIN;
            const clientId = config.clientId;
            const redirectSignOut = import.meta.env.VITE_OAUTH_REDIRECT_SIGN_OUT;

            if (!domain.startsWith('http')) {
                domain = `https://${domain}`;
            }

            const logoutUrl = `${domain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(redirectSignOut)}`;
            window.location.href = logoutUrl;
        }
    },

    isAuthenticated() {
        return !!localStorage.getItem('accessToken');
    },

    getTokens() {
        return {
            accessToken: localStorage.getItem('accessToken'),
            idToken: localStorage.getItem('idToken'),
            refreshToken: localStorage.getItem('refreshToken'),
        };
    },

    signInWithRedirect(provider) {
        let domain = import.meta.env.VITE_COGNITO_DOMAIN;
        const redirectSignIn = import.meta.env.VITE_OAUTH_REDIRECT_SIGN_IN;
        const clientId = config.clientId;

        if (!domain.startsWith('http')) {
            domain = `https://${domain}`;
        }

        console.log("Debug OAuth Config:", { domain, redirectSignIn, clientId, provider });

        // Ensure domain doesn't have https:// prefix if it's already in the variable, or handle it
        // Usually Cognito domain is like: https://your-domain.auth.us-east-1.amazoncognito.com
        // The Hosted UI URL format:
        // https://<your-domain>/oauth2/authorize?response_type=code&client_id=<your-client-id>&redirect_uri=<your-redirect-uri>&identity_provider=<provider>

        const url = `${domain}/oauth2/authorize?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectSignIn)}&identity_provider=${provider}&scope=email+openid+profile`;

        console.log("Redirecting to:", url);

        window.location.href = url;
    },

    async handleCodeExchange(code) {
        let domain = import.meta.env.VITE_COGNITO_DOMAIN;
        const redirectSignIn = import.meta.env.VITE_OAUTH_REDIRECT_SIGN_IN;
        const clientId = config.clientId;

        if (!domain.startsWith('http')) {
            domain = `https://${domain}`;
        }

        const params = new URLSearchParams();
        params.append('grant_type', 'authorization_code');
        params.append('client_id', clientId);
        params.append('code', code);
        params.append('redirect_uri', redirectSignIn);

        const response = await fetch(`${domain}/oauth2/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params
        });

        if (!response.ok) {
            throw new Error('Failed to exchange code for tokens');
        }

        const tokens = await response.json();

        localStorage.setItem('accessToken', tokens.access_token);
        localStorage.setItem('idToken', tokens.id_token);
        if (tokens.refresh_token) {
            localStorage.setItem('refreshToken', tokens.refresh_token);
        }

        return tokens;
    }
};
