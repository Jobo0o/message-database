# Hostaway API Authentication

This document provides information about the authentication mechanism used for the Hostaway API in the Message Database application.

## Authentication Method

The application uses **OAuth 2.0 Client Credentials Flow** to authenticate with the Hostaway API. This is the official authentication method according to the Hostaway API documentation.

## Configuration

To use the OAuth authentication flow, you need to set the following environment variables:

- `HOSTAWAY_CLIENT_ID`: Your Hostaway account ID
- `HOSTAWAY_CLIENT_SECRET`: Client secret from your Hostaway dashboard

You can set these variables in your `.env` file or export them directly in your environment.

## How Authentication Works

1. **Token Request**: The application requests an access token by sending a POST request to `https://api.hostaway.com/v1/accessTokens` with the client credentials.

2. **Token Response**: Hostaway responds with a token that is valid for 24 months.

3. **Token Caching**: The application caches this token in memory until it expires, to avoid requesting a new token for each API call.

4. **Token Usage**: All API requests include the token in the Authorization header: `Authorization: Bearer <access_token>`.

5. **Token Refresh**: If a request returns a 401 or 403 error, the application will automatically attempt to refresh the token.

## Troubleshooting

If you encounter authentication issues, check the following:

1. Verify that your client ID and client secret are correct
2. Ensure your Hostaway account has access to the API
3. Check if your token has expired (the application should handle this automatically)
4. Look for 401 or 403 error responses in the logs

## Example Token Request

```bash
curl -X POST \
  https://api.hostaway.com/v1/accessTokens \
  -H 'Cache-control: no-cache' \
  -H 'Content-type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials&client_id=YOUR_ACCOUNT_ID&client_secret=YOUR_CLIENT_SECRET&scope=general'
```

Example response:

```json
{
    "token_type": "Bearer",
    "expires_in": 15897600,
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0..."
}
``` 