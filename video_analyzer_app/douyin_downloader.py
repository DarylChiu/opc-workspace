#!/usr/bin/env python3
"""
Douyin 视频下载器 V4 — 轻量版
1. urllib 抓取 iesdouyin.com 页面提取 video_id
2. curl 下载 playwm 视频流
3. Playwright 作为 fallback（页面需要 JS 时才用）
"""
import sys, os, time, subprocess, shutil, tempfile, re, urllib.request, http.cookiejar

def _validate_video(path: str) -> bool:
    r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=codec_type","-of","csv=p=0", path],
        capture_output=True, text=True, timeout=10)
    return r.stdout.strip() == "video"

def _extract_video_id_from_page(url: str) -> str:
    """从 iesdouyin.com 页面 HTML 提取 video_id"""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Referer': 'https://www.iesdouyin.com/',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = opener.open(req, timeout=15)
        html = resp.read().decode('utf-8', errors='ignore')
        ms = re.findall(r'video_id["=:]+([a-zA-Z0-9_]+)', html)
        if ms:
            print(f"[DOUYIN] 页面提取 video_id: {ms[0]}")
            return ms[0]
    except Exception as e:
        print(f"[DOUYIN] 页面抓取失败: {e}")
    return ""

def _download_playwm(video_id: str, output_path: str) -> bool:
    """下载 playwm 视频"""
    if not video_id:
        return False
    
    # 尝试多个画质
    for ratio in ['1080p', '720p', '540p', '480p']:
        play_url = f"https://www.iesdouyin.com/aweme/v1/playwm/?video_id={video_id}&ratio={ratio}&line=0"
        print(f"[DOUYIN] 尝试 {ratio}: {play_url[:120]}")
        
        tmp = output_path + ".tmp"
        r = subprocess.run([
            "curl","-L","-o",tmp,
            "-A","Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
            "-H","Referer: https://www.iesdouyin.com/",
            "--max-time","120",
            play_url
        ], capture_output=True, text=True, timeout=130)
        
        if os.path.exists(tmp) and os.path.getsize(tmp) > 10240:
            if _validate_video(tmp):
                shutil.move(tmp, output_path)
                size_mb = os.path.getsize(output_path)/(1024*1024)
                print(f"[DOUYIN] ✅ 下载成功 ({ratio}): {size_mb:.1f}MB")
                return True
            else:
                print(f"[DOUYIN] ⚠️ 无效视频流 ({ratio})")
                os.remove(tmp)
        else:
            sz = os.path.getsize(tmp) if os.path.exists(tmp) else 0
            print(f"[DOUYIN] ⚠️ 下载失败 ({ratio}): {sz} bytes")
            if os.path.exists(tmp): os.remove(tmp)
    
    return False

def _download_with_playwright(url: str, output_path: str) -> bool:
    """Playwright fallback：拦截 playwm 请求"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[DOUYIN] Playwright 未安装")
        return False
    
    td = tempfile.mkdtemp(prefix="dy_pw_")
    try:
        with sync_playwright() as p:
            playwm_urls = []
            
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled','--no-sandbox','--mute-audio']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
                viewport={"width":390,"height":844}, locale="zh-CN", timezone_id="Asia/Shanghai"
            )
            context.add_init_script("""
                Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
            """)
            page = context.new_page()
            
            def on_request(request):
                u = request.url
                if '/aweme/v1/play' in u:
                    playwm_urls.append(u)
                    print(f"[DOUYIN] PW拦截: {u[:150]}")
            
            page.on('request', on_request)
            
            print(f"[DOUYIN] PW loading: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
            except: pass
            
            # 等最多 12 秒
            for _ in range(12):
                time.sleep(1)
                if playwm_urls: break
            
            browser.close()
            
            if not playwm_urls:
                return False
            
            # 下载
            for i, pu in enumerate(playwm_urls[:3]):
                tmp = os.path.join(td, f"tmp_{i}.mp4")
                r = subprocess.run([
                    "curl","-L","-o",tmp,
                    "-A","Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
                    "-H","Referer: https://www.iesdouyin.com/",
                    "--max-time","120",
                    pu
                ], capture_output=True, text=True, timeout=130)
                
                if os.path.exists(tmp) and os.path.getsize(tmp) > 10240:
                    if _validate_video(tmp):
                        shutil.move(tmp, output_path)
                        print(f"[DOUYIN] ✅ PW下载成功: {os.path.getsize(output_path)/1024/1024:.1f}MB")
                        return True
    finally:
        try: shutil.rmtree(td)
        except: pass
    
    return False

def download_douyin_video(url: str, output_path: str) -> bool:
    # 确保使用 iesdouyin.com
    if 'iesdouyin.com' not in url:
        # 从 shortlink 或 douyin.com URL 提取 share_id
        m = re.search(r'[/=](\d{15,20})', url)
        if m:
            url = f"https://www.iesdouyin.com/share/video/{m.group(1)}/"
        # 也尝试从 v.douyin.com shortlink 重定向
        if 'v.douyin.com' in url:
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                resp = urllib.request.urlopen(req, timeout=10)
                final = resp.url
                m = re.search(r'/video/(\d+)', final)
                if m:
                    url = f"https://www.iesdouyin.com/share/video/{m.group(1)}/"
                    print(f"[DOUYIN] shortlink → {url}")
            except: pass
    
    video_id = _extract_video_id_from_page(url)
    
    if video_id:
        if _download_playwm(video_id, output_path):
            return True
        print("[DOUYIN] playwm 直接下载失败，尝试 Playwright...")
    
    # Playwright fallback
    return _download_with_playwright(url, output_path)

if __name__ == "__main__":
    success = download_douyin_video(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
