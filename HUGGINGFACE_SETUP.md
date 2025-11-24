# HuggingFace Inference API Setup Guide

This guide explains how to set up and use the HuggingFace Inference API with the Gym Membership Chatbot.

## Overview

The chatbot now uses **HuggingFace Inference API** instead of local Ollama, providing:

✅ **No local model downloads** - Models run on HuggingFace servers
✅ **Works on Render** - Perfect for cloud deployment
✅ **Free tier available** - Mistral-7B is free with limitations
✅ **Fast responses** - HuggingFace infrastructure is optimized
✅ **Easy configuration** - Just set an API key
✅ **Multiple model choices** - Switch models anytime

---

## Step 1: Create a HuggingFace Account

1. Go to [huggingface.co](https://huggingface.co)
2. Click **Sign up** and create a free account
3. Verify your email address

---

## Step 2: Generate an API Token

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click **New token**
3. Set the name to something like `gym-chatbot`
4. Select **Read** access (sufficient for inference)
5. Click **Generate**
6. Copy the token (starts with `hf_`)

**⚠️ Important**: Keep this token secret! Never commit it to GitHub.

---

## Step 3: Configure Environment Variables

### For Local Development

Create or update your `.env` file in the project root:

```env
HF_API_KEY=hf_your_token_here_replace_with_actual_token
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

### For Docker

Update `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      HF_API_KEY: hf_your_token_here
      HF_MODEL: mistralai/Mistral-7B-Instruct-v0.2
```

### For Render.com

1. Go to your Render project dashboard
2. Navigate to **Environment**
3. Add a new environment variable:
   - **Key**: `HF_API_KEY`
   - **Value**: Your HuggingFace token
4. Add another for model selection (optional):
   - **Key**: `HF_MODEL`
   - **Value**: `mistralai/Mistral-7B-Instruct-v0.2`
5. Click **Save**

---

## Step 4: Available Models

### Recommended Models

| Model | Model ID | Free Tier | Speed | Quality | Notes |
|-------|----------|-----------|-------|---------|-------|
| Mistral 7B | `mistralai/Mistral-7B-Instruct-v0.2` | ✅ Yes | ⚡ Fast | ⭐⭐⭐⭐ | **Recommended** - Best for gym FAQs |
| Llama 2 | `meta-llama/Llama-2-7b-chat-hf` | ✅ Yes* | ⚡ Fast | ⭐⭐⭐⭐⭐ | Requires model acceptance |
| Falcon | `tiiuae/falcon-7b-instruct` | ✅ Yes | ⚡ Very Fast | ⭐⭐⭐⭐ | Good alternative |
| GPT-2 | `gpt2` | ✅ Yes | ⚡ Very Fast | ⭐⭐⭐ | Testing/lightweight option |

*Llama 2 requires you to accept the model's license on HuggingFace first

### Mistral-7B (Default, Recommended)

**Pros:**
- Free tier available
- Excellent quality responses
- Fast inference
- No license agreements needed
- Perfect for customer service

**Cons:**
- May have occasional rate limits on free tier

**Setup:**
```env
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

### Llama 2

**Pros:**
- Highest quality responses
- Strong instruction following
- Community-supported

**Cons:**
- Requires license acceptance on HuggingFace
- Slightly slower than Mistral

**Setup:**
1. Go to [meta-llama/Llama-2-7b-chat-hf](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf)
2. Click "Agree and access repository"
3. Accept the license
4. Update your `.env`:
   ```env
   HF_MODEL=meta-llama/Llama-2-7b-chat-hf
   ```

### Falcon 7B

**Pros:**
- Very fast
- Good quality
- Low latency

**Setup:**
```env
HF_MODEL=tiiuae/falcon-7b-instruct
```

### Testing with GPT-2

For lightweight testing or when quotas are exceeded:

```env
HF_MODEL=gpt2
```

---

## Step 5: Test the Setup

### Local Testing

1. Create `.env` file with your API key:
   ```bash
   echo 'HF_API_KEY=hf_your_token_here' > .env
   echo 'HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2' >> .env
   ```

2. Run Django:
   ```bash
   python manage.py runserver
   ```

3. Go to http://localhost:8000/chatbot/

4. Try asking: "What membership plans do you offer?"

### Docker Testing

1. Update `docker-compose.yml` with your API key
2. Run:
   ```bash
   docker-compose up -d web
   docker-compose logs -f web
   ```
3. Visit http://localhost:8000/chatbot/

### Check HuggingFace Status

```bash
python manage.py shell
>>> from gym_app.chatbot import GymChatbot
>>> GymChatbot.check_hf_status()
{'status': 'configured', 'message': 'HuggingFace API is configured and ready'}
```

---

## Step 6: Deploy to Render

### Option 1: Environment Variables (Recommended)

1. Go to Render dashboard → Your service
2. Click **Environment**
3. Add `HF_API_KEY` with your token value
4. Redeploy the service

### Option 2: Using .env File

1. Create `.env` with HuggingFace credentials
2. Add to `.gitignore` (never commit secrets!)
3. Upload `.env` file to Render (instructions vary by deployment method)

---

## Troubleshooting

### "HuggingFace API key not configured"

**Problem**: The environment variable isn't set

**Solution**:
```bash
# Check if HF_API_KEY is set
echo $HF_API_KEY

# If empty, set it
export HF_API_KEY=hf_your_token_here
```

### "401 Unauthorized" or "Invalid API key"

**Problem**: The API key is wrong or expired

**Solution**:
1. Verify your token at https://huggingface.co/settings/tokens
2. Generate a new token if needed
3. Update the environment variable
4. Restart the app

### "Model not found"

**Problem**: The model ID is incorrect or you don't have access

**Solution**:
1. Check the model exists: https://huggingface.co/models
2. For gated models (like Llama 2), accept the license first
3. Verify the exact model ID

### "Rate limit exceeded"

**Problem**: Free tier quota was exceeded

**Solution**:
- **Short term**: Wait a few hours or use a smaller model
- **Long term**: Upgrade to HuggingFace Pro ($9/month) for higher limits
- **Alternative**: Use a different model

### Slow responses

**Problem**: Model inference is taking too long

**Solution**:
1. Switch to a faster model:
   ```env
   HF_MODEL=tiiuae/falcon-7b-instruct
   ```

2. Reduce max tokens:
   - Edit `gym_app/chatbot.py`
   - Change `MAX_TOKENS = 256` (even lower, like 128)

3. Check HuggingFace status: https://status.huggingface.co

### "Connection timeout"

**Problem**: HuggingFace servers not responding

**Solution**:
1. Check HuggingFace status: https://status.huggingface.co
2. Retry in a moment
3. Try a different model

---

## API Usage & Costs

### Free Tier (Default)

- **Cost**: Free
- **Limits**:
  - Fair-use policy applies
  - ~1000s of free inferences
  - Rate limited during high traffic
- **Best for**: Personal projects, low-traffic apps

### HuggingFace Pro ($9/month)

- **Cost**: $9 USD
- **Limits**:
  - Higher rate limits
  - Priority access to models
  - Better uptime guarantees
- **Best for**: Production applications

### Monitoring Your Usage

1. Go to https://huggingface.co/settings/billing/overview
2. View your inference usage
3. Check remaining free credits

---

## Environment Variable Reference

| Variable | Required | Default | Example |
|----------|----------|---------|---------|
| `HF_API_KEY` | ✅ Yes | None | `hf_abc123xyz...` |
| `HF_MODEL` | ❌ No | `mistralai/Mistral-7B-Instruct-v0.2` | `meta-llama/Llama-2-7b-chat-hf` |
| `HF_API_URL` | ❌ No | `https://api-inference.huggingface.co` | Same (rarely changed) |

---

## Security Best Practices

⚠️ **Never:**
- Commit API keys to Git
- Share API tokens publicly
- Use API keys in frontend code

✅ **Always:**
- Use environment variables for secrets
- Rotate tokens periodically
- Use `.gitignore` to exclude `.env`
- Restrict token permissions to "Read only"

---

## Switching Models

To change the model:

1. **Local**: Edit `.env`
   ```env
   HF_MODEL=meta-llama/Llama-2-7b-chat-hf
   ```

2. **Docker**: Update `docker-compose.yml`
   ```yaml
   environment:
     HF_MODEL: meta-llama/Llama-2-7b-chat-hf
   ```

3. **Render**: Update Environment variable in dashboard
   - Set `HF_MODEL=meta-llama/Llama-2-7b-chat-hf`
   - Redeploy

3. Restart the application - no code changes needed!

---

## Comparing with Previous Setup

### Before (Ollama)
❌ Requires 4GB+ RAM locally
❌ Doesn't work on Render (resource-intensive)
❌ Need to pull ~4GB model files
❌ 30-60s cold starts
❌ Only works with Ollama models

### After (HuggingFace)
✅ No local resources needed
✅ Works perfectly on Render
✅ Models served by HuggingFace
✅ Fast responses (<5s typically)
✅ Access to hundreds of models
✅ Easy scaling and updates

---

## Next Steps

1. **Get API Key**: https://huggingface.co/settings/tokens
2. **Set Environment Variable**: Add `HF_API_KEY`
3. **Test Locally**: Run the chatbot and test
4. **Deploy**: Push to Render
5. **Monitor**: Check HuggingFace usage

---

## Support & Resources

- **HuggingFace Docs**: https://huggingface.co/docs/inference-api
- **Available Models**: https://huggingface.co/models
- **Status Page**: https://status.huggingface.co
- **Community**: https://discuss.huggingface.co

---

## FAQ

**Q: Is HuggingFace free?**
A: Yes! Free tier includes inference for personal/research projects. Pro tier ($9/month) for production.

**Q: Can I use my own models?**
A: Yes, if you host them on HuggingFace. You can also fine-tune Mistral/Llama and deploy.

**Q: What if I exceed rate limits?**
A: Wait a few hours, upgrade to Pro, or use a smaller model.

**Q: Can I go back to Ollama?**
A: Yes! The code is easily reversible. Just switch back to the Ollama imports.

**Q: Will this work on Render's free tier?**
A: Yes! HuggingFace free tier works with Render free tier.

**Q: How fast is it?**
A: Typically 1-5 seconds for responses, depending on model and load.

**Q: Can I use multiple models?**
A: Yes, change `HF_MODEL` environment variable anytime. No code changes needed.
