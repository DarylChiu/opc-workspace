#!/usr/bin/env python3
"""使用 Playwright 直接下载 Douyin 视频（绕过 yt-dlp 提取器）
V2: 智能 URL 选择 + 视频验证"""
import sys, os, time, subprocess, shutil, tempfile, re

def _validate_video(path: str) -> bool:
    """检查文件是否包含真正的视频流"""
    r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=codec_type","-of","csv=p=0", path],
        capture_output=True, text=True, timeout=10)
    return r.stdout.strip() == "video"

def download_douyin_video(url: str, output_path: str) -> bool:
    from playwright.sync_api import sync_playwright
    
    td = tempfile.mkdtemp(prefix="dy_dl_")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled','--no-sandbox']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width":1440,"height":900}, locale="zh-CN", timezone_id="Asia/Shanghai"
            )
            context.add_init_script("""
                Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
                window.chrome={runtime:{}};
            """)
            page = context.new_page()
            
            # 拦截视频请求：按优先级排序
            video_urls = []
            def on_response(response):
                ct = response.headers.get('content-type','')
                u = response.url
                # 只收集可能的视频 URL
                if ('video' in ct or 'octet-stream' in ct or 'mp4' in ct):
                    # 过滤明显的音频流
                    if 'audio' in ct.lower() and 'video' not in ct.lower():
                        return
                    # URL 路径检查
                    if any(k in u for k in ('/video/','/aweme/','v26','douyinvod','zjcdn')):
                        video_urls.append(u)
                        print(f"[DOUYIN] 拦截: {u[:100]}")
            
            page.on('response', on_response)
            
            print(f"[DOUYIN] Loading: {url}")
            try:
                page.goto(url, wait_until="commit", timeout=60000)
            except: pass
            time.sleep(6)
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except: pass
            time.sleep(3)
            
            # 尝试点击播放触发视频加载
            try:
                page.click('video, [class*=video], [class*=player]', timeout=5000)
            except: pass
            time.sleep(4)
            
            # Fallback: extract from DOM
            if not video_urls:
                try:
                    src = page.evaluate("""
                        () => {
                            const v = document.querySelector('video');
                            if(v&&v.src) return v.src;
                            const sources = document.querySelectorAll('source');
                            for(let s of sources) if(s.src.includes('video')) return s.src;
                            return '';
                        }
                    """)
                    if src: video_urls.append(src)
                except: pass
            
            if not video_urls:
                # Last resort: page content search
                content = page.content()
                for pat in [
                    r'https?://[^"\'<>]+/(?:video|aweme|play)/[^"\'<>]+\.(?:mp4|m3u8)[^"\'<>]*',
                    r'https?://[^"\'<>]+\.zjcdn\.com[^"\'<>]+',
                    r'https?://[^"\'<>]+douyinvod[^"\'<>]+',
                ]:
                    ms = set(re.findall(pat, content))
                    video_urls.extend(ms)
                    if ms: break
            
            browser.close()
            
            if not video_urls:
                print("[DOUYIN] No video URLs found")
                return False
            
            # 依次尝试下载，第一个通过验证的才保留
            for i, vu in enumerate(video_urls[:10]):
                print(f"[DOUYIN] 尝试 #{i+1}: {vu[:100]}")
                tmp = os.path.join(td, f"tmp_{i}.mp4")
                r = subprocess.run([
                    "curl","-L","-o",tmp,
                    "-A","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    vu
                ], capture_output=True, text=True, timeout=120)
                
                if not os.path.exists(tmp) or os.path.getsize(tmp) < 1024:
                    continue
                
                if _validate_video(tmp):
                    shutil.move(tmp, output_path)
                    size_mb = os.path.getsize(output_path)/(1024*1024)
                    print(f"[DOUYIN] ✅ 下载成功: {size_mb:.1f}MB (含视频流)")
                    return True
                else:
                    print(f"[DOUYIN] ⚠️  无视频流，跳过")
            
            print(f"[DOUYIN] ❌ 所有 URL 都无有效视频流")
            return False
    
    finally:
        try: shutil.rmtree(td)
        except: pass

if __name__ == "__main__":
    success = download_douyin_video(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
