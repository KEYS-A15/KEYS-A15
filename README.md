## ![gitgif (2)](https://github.com/KEYS-A15/KEYS-A15/assets/78949462/635cf704-ecbd-421d-8dad-1b2a2e05d091)

<div align='center'>I work for Innovation.</div>
connect with me.<br>
gajjar.shrey@proton.me

<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <style>
    body {
      background-color: #0d0d0d;
      color: #00ff88;
      font-family: 'Courier New', Courier, monospace;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }

    .terminal {
      background-color: #0d0d0d;
      padding: 20px;
      border-radius: 5px;
      box-shadow: 0 0 10px #00ff88;
      font-size: 1.2rem;
      white-space: pre;
    }

    .cursor {
      display: inline-block;
      width: 10px;
      background-color: #00ff88;
      animation: blink 1s infinite;
      margin-left: 2px;
    }

    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0; }
    }
  </style>
</head>
<body>
  <div class="terminal">
    <span id="typed"></span><span class="cursor"></span>
  </div>

  <script>
    const lines = [
      "Initializing...",
      "Welcome, I’m Mr. Stark 👨‍💻",
      "Senior AI Developer 🚀",
      "I build outside-the-box ML solutions 🤖",
      "Let's talk innovation 💡"
    ];

    let currentLine = 0;
    let currentChar = 0;
    const typedSpan = document.getElementById('typed');

    function typeLine() {
      if (currentLine < lines.length) {
        const line = lines[currentLine];
        if (currentChar < line.length) {
          typedSpan.textContent += line.charAt(currentChar);
          currentChar++;
          setTimeout(typeLine, 50);
        } else {
          typedSpan.innerHTML += '<br>';
          currentLine++;
          currentChar = 0;
          setTimeout(typeLine, 500);
        }
      }
    }

    typeLine();
  </script>
</body>
</html>
