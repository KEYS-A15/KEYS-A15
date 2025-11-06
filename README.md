<!--HTML template for GitHub README with animation like a terminal effect-->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>GitHub-style Banner — Terminal Animation</title>
    <style>
        :root{
            --bg:#0f1724;
            --card:#0b1220;
            --muted:#94a3b8;
            --accent:#7dd3fc;
            --glass: rgba(255,255,255,0.03);
            --radius:12px;
            --typing-speed:35; /* ms per char */
        }

        html,body{height:100%;margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif;background:linear-gradient(180deg,#071426 0%, #0f2a3f 100%);color:#e6eef6;}
        .wrapper{
            min-height:100%;
            display:flex;
            align-items:center;
            justify-content:center;
            padding:48px 20px;
            box-sizing:border-box;
            gap:24px;
            animation:fadeIn .9s ease both;
        }

        /* Card / Banner */
        .banner{
            width:min(980px,96%);
            background:linear-gradient(180deg,var(--card), #08101b 60%);
            border-radius:var(--radius);
            box-shadow:0 10px 30px rgba(2,6,23,0.6), inset 0 1px 0 rgba(255,255,255,0.02);
            overflow:hidden;
            display:flex;
            gap:0;
            transform:translateY(6px);
            animation:pop .6s cubic-bezier(.2,.9,.3,1) .05s both;
        }

        .left{
            flex:1 1 60%;
            padding:28px 32px;
            box-sizing:border-box;
            display:flex;
            flex-direction:column;
            gap:18px;
            background:linear-gradient(90deg, rgba(255,255,255,0.015), transparent);
        }

        .title{
            display:flex;
            align-items:center;
            gap:12px;
        }
        .logo{
            width:56px;height:56px;border-radius:10px;background:linear-gradient(135deg,var(--accent),#60a5fa);
            display:flex;align-items:center;justify-content:center;font-weight:700;color:#001f2a;
            box-shadow:0 6px 18px rgba(109,117,120,0.12), inset 0 -6px 18px rgba(255,255,255,0.02);
            font-family:monospace;
        }
        .heading{
            display:flex;flex-direction:column;
            gap:2px;
        }
        h1{margin:0;font-size:1.15rem;letter-spacing:-0.2px}
        p.lead{margin:0;color:var(--muted);font-size:0.95rem}

        /* Terminal */
        .terminal-wrap{
            flex:1 1 40%;
            background:linear-gradient(180deg,#00121b 0%,#021726 100%);
            padding:16px;
            display:flex;
            flex-direction:column;
            gap:14px;
            min-width:320px;
        }

        .term-top{
            display:flex;align-items:center;gap:8px;
            padding:6px 8px;border-radius:8px;background:linear-gradient(180deg,rgba(255,255,255,0.02),transparent);
            box-shadow:inset 0 -1px 0 rgba(255,255,255,0.02);
        }
        .dots{display:flex;gap:6px}
        .dot{width:12px;height:12px;border-radius:50%}
        .dot.r{background:#ff5f56}
        .dot.y{background:#ffbd2e}
        .dot.g{background:#27c93f}

        .term{
            background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00));
            border-radius:8px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,monospace;color:#cfefff;font-size:13.5px;line-height:1.5;
            box-shadow:inset 0 1px 0 rgba(255,255,255,0.02), 0 8px 20px rgba(2,6,23,0.45);
            min-height:140px; display:flex;align-items:flex-start;
            overflow:hidden; position:relative;
        }

        /* type lines */
        .typed{white-space:pre-wrap;word-break:break-word}
        .prompt{color:#7ee3b8;margin-right:8px}
        .cursor{
            display:inline-block;width:8px;height:18px;background:#cfefff;margin-left:6px;border-radius:2px;vertical-align:bottom;
            animation:blink 1s steps(2, start) infinite;
            transform-origin:left bottom;
        }

        /* small subtitle / badges */
        .meta{display:flex;gap:8px;flex-wrap:wrap}
        .badge{background:var(--glass);color:var(--muted);padding:6px 10px;border-radius:999px;font-size:12px}

        @keyframes blink{50%{opacity:0}}
        @keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
        @keyframes pop{from{opacity:0;transform:translateY(18px) scale(.995)}to{opacity:1;transform:none}}

        /* Responsive */
        @media (max-width:720px){
            .banner{flex-direction:column}
            .terminal-wrap{order:-1}
        }
    </style>
</head>
<body>
    <div class="wrapper" role="main" aria-label="GitHub styled banner with terminal demo">
        <section class="banner" aria-labelledby="banner-title">
            <div class="left">
                <div class="title">
                    <div class="logo" aria-hidden="true">GH</div>
                    <div class="heading">
                        <h1 id="banner-title">Project README Banner</h1>
                        <p class="lead">A compact GitHub-style banner with a terminal-like animated snippet.</p>
                    </div>
                </div>

                <div class="meta" aria-hidden="true">
                    <span class="badge">JavaScript</span>
                    <span class="badge">HTML</span>
                    <span class="badge">CSS</span>
                </div>
            </div>

            <aside class="terminal-wrap" aria-label="Terminal preview">
                <div class="term-top" aria-hidden="true">
                    <div class="dots" title="window controls">
                        <div class="dot r"></div>
                        <div class="dot y"></div>
                        <div class="dot g"></div>
                    </div>
                    <div style="flex:1"></div>
                    <div style="color:var(--muted);font-size:12px">bash</div>
                </div>

                <div class="term" id="terminal" role="log" aria-live="polite">
                    <div class="typed" id="typed"></div><span class="cursor" aria-hidden="true"></span>
                </div>
            </aside>
        </section>
    </div>

    <script>
        // GitHub Copilot style: small typewriter renderer
        (function(){
            const lines = [
                {prompt:'$', text:' git clone https://github.com/username/project.git'},
                {prompt:'$', text:' cd project'},
                {prompt:'$', text:' npm install'},
                {prompt:'$', text:' npm run dev'},
                {prompt:'✓', text:' Open http://localhost:3000 — enjoy!'}
            ];

            const out = document.getElementById('typed');
            const cursor = document.querySelector('.cursor');
            const speed = Number(getComputedStyle(document.documentElement).getPropertyValue('--typing-speed')) || 35;

            let lineIndex = 0, charIndex = 0, showing = '';

            function typeStep(){
                const current = lines[lineIndex];
                if(!current) return; // nothing
                if(charIndex === 0){
                    // prepend prompt
                    showing += current.prompt + ' ';
                }

                const target = current.text;
                if(charIndex < target.length){
                    showing += target[charIndex++];
                    out.textContent = showing;
                    scrollBottom();
                    setTimeout(typeStep, speed + Math.random()*40);
                } else {
                    // finished line: advance after a pause
                    lineIndex++;
                    charIndex = 0;
                    showing += '\n';
                    out.textContent = showing;
                    scrollBottom();
                    setTimeout(()=>{
                        if(lineIndex < lines.length){
                            setTimeout(typeStep, 400);
                        } else {
                            // finished all lines: show final state and keep cursor blinking, then loop after pause
                            setTimeout(()=>resetLoop(), 1800);
                        }
                    }, 220);
                }
            }

            function resetLoop(){
                // simple fade-out animation by clearing characters progressively for a loop effect
                let i = 0;
                const interval = setInterval(()=>{
                    if(i > 10){ clearInterval(interval); showing=''; out.textContent=''; lineIndex=0; charIndex=0; setTimeout(typeStep,300); return; }
                    // slight shrink effect (not perfect but gives rhythm)
                    i++;
                }, 60);
            }

            function scrollBottom(){
                const term = document.getElementById('terminal');
                term.scrollTop = term.scrollHeight;
            }

            // start typing after a short delay
            setTimeout(typeStep, 700);

            // Improve accessibility: announce first line when loaded
            out.setAttribute('aria-atomic','false');
        })();
    </script>
</body>
</html>
