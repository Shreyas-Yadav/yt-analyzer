# S3 Deployment & CloudFront Guide

## Why CloudFront is Needed

### Problem 1: S3 Doesn't Support HTTPS 🔒

When you enable S3 static website hosting, you get a URL like:
```
http://your-bucket.s3-website-us-east-1.amazonaws.com
```

Notice it's **HTTP** (not HTTPS).

**The Issue:**
- Google OAuth **requires HTTPS** for redirect URLs in production
- Browsers block OAuth on HTTP sites (security risk)
- Your Google Sign-In **will fail** without HTTPS

### Problem 2: React Router Breaks on S3 🔀

When a user visits `your-site.com/login` directly:
- S3 looks for a file called `/login/index.html`
- That file doesn't exist (it's all in one `index.html`)
- User gets a 404 error

**React Router needs the server to always return `index.html`**, but S3 can't do this properly.

## How CloudFront Solves Both Problems

CloudFront is AWS's **Content Delivery Network (CDN)** that sits in front of your S3 bucket:

### ✅ Provides HTTPS
- CloudFront gives you `https://d111111abcdef8.cloudfront.net`
- Or you can use your custom domain with SSL certificate
- Google OAuth works perfectly

### ✅ Fixes Routing
- You configure CloudFront to return `index.html` for all routes
- Users can bookmark/refresh any page without errors

### ✅ Bonus: Better Performance
- Caches your files globally (faster load times)
- Free HTTPS certificate via AWS Certificate Manager

## Simple Analogy

- **S3** = Storage box (just holds your files)
- **CloudFront** = Delivery service with security guards (HTTPS + smart routing)

---

## Deployment Checklist

### 1. Environment Variables
Create a `.env.production` file with your production URLs:
```bash
VITE_COGNITO_USER_POOL_ID=us-east-1_tMPaajzoZ
VITE_COGNITO_USER_POOL_CLIENT_ID=2t2c4j5psuanvub03uv07cofml
VITE_COGNITO_DOMAIN=us-east-1tmpaajzoz.auth.us-east-1.amazoncognito.com
VITE_OAUTH_REDIRECT_SIGN_IN=https://your-cloudfront-or-s3-url/
VITE_OAUTH_REDIRECT_SIGN_OUT=https://your-cloudfront-or-s3-url/login
```

### 2. AWS Cognito Console
Update your Cognito App Client settings:
- **Allowed callback URLs**: Add your CloudFront/S3 URL (e.g., `https://d111111abcdef8.cloudfront.net/`)
- **Allowed sign-out URLs**: Add your URL + `/login`
- Keep the localhost URLs if you want to keep testing locally

### 3. S3 Bucket Configuration
- Enable **Static Website Hosting**
- Set **Index document**: `index.html`
- Set **Error document**: `index.html` (important for React Router!)
- Configure bucket policy for public read access

### 4. CloudFront Configuration (Recommended)
- Create a CloudFront distribution pointing to your S3 bucket
- Set **Custom Error Responses**:
  - 404 → return `/index.html` with 200 status
  - 403 → return `/index.html` with 200 status
- This ensures React Router works on all routes

### 5. Build Process
```bash
npm run build
```
Vite will use the production env variables and create the `dist` folder.

### 6. Upload to S3
Upload the contents of the `dist` folder to your S3 bucket.

---

**Bottom Line:** Without CloudFront (or another HTTPS solution), your Google OAuth won't work in production!
