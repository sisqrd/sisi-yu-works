import re, shutil, os, sys
# Usage: python3 tools/build.py   (from the repo root)
# Turns src/page.html (the page as designed in Claude) into site/index.html for Netlify.
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src", "page.html")
out = os.path.join(root, "site")
os.makedirs(out, exist_ok=True)
html = open(src, encoding="utf-8").read()
html = html.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')

# --- reactions: CSS, markup, script (Netlify Forms) ---
css = """
/* reactions (Netlify Forms) */
.react{margin-top:44px; padding-top:28px; border-top:1px dashed var(--line); max-width:720px}
.react h3{font-family:var(--f-display); font-weight:800; font-size:24px; letter-spacing:-.02em; margin:6px 0 14px}
.react-row{display:flex; flex-wrap:wrap; gap:10px}
.react-row button{all:unset; box-sizing:border-box; cursor:pointer; display:inline-flex; align-items:center; gap:8px; padding:10px 14px; border:1.5px solid var(--ink); background:var(--card); color:var(--ink); font-family:var(--f-mono); font-size:13px; border-radius:2px; box-shadow:3px 3px 0 var(--ink); transition:transform .12s, box-shadow .12s}
.react-row button:hover{transform:translate(-1px,-1px); box-shadow:4px 4px 0 var(--flare)}
.react-row button[aria-pressed="true"]{background:var(--cobalt); border-color:var(--cobalt); color:var(--on-accent); box-shadow:3px 3px 0 var(--ink)}
.react-row button:focus-visible{outline:2px solid var(--flare); outline-offset:3px}
.react-row button span{font-size:16px; line-height:1}
.react-note{display:flex; flex-wrap:wrap; gap:10px; margin-top:14px}
.react-note input{flex:1 1 260px; min-width:0; font:inherit; font-size:15px; padding:11px 12px; border:1px solid var(--line); background:var(--card); color:var(--ink); border-radius:2px}
.react-note input:focus{outline:2px solid var(--cobalt); outline-offset:1px}
.react-note .send{all:unset; cursor:pointer; box-sizing:border-box; padding:11px 16px; background:var(--ink); color:var(--paper); font-family:var(--f-mono); font-size:13px; text-transform:uppercase; letter-spacing:.04em; border-radius:2px}
.react-note .send:hover{background:var(--flare)}
.react-note .send[disabled]{opacity:.5; cursor:default}
.react-status{font-family:var(--f-mono); font-size:12px; color:var(--ink-2); margin-top:10px; min-height:1.4em}
.react-status.ok{color:var(--cobalt)} .react-status.err{color:var(--flare)}
.sr-only{position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap}
"""
html = html.replace("</style>", css + "</style>", 1)

markup = """    <form class="react" id="reactForm" name="reaction" method="POST" data-netlify="true" netlify-honeypot="bot-field">
      <input type="hidden" name="form-name" value="reaction">
      <p class="sr-only"><label>Leave this empty <input name="bot-field" tabindex="-1" autocomplete="off"></label></p>
      <input type="hidden" name="reaction" id="reactValue">
      <span class="mono">Leave a reaction</span>
      <h3>Liked something? Tell me in one click.</h3>
      <div class="react-row" role="group" aria-label="Pick a reaction">
        <button type="button" data-r="Love it" aria-pressed="false"><span aria-hidden="true">👏</span>Love it</button>
        <button type="button" data-r="Inspiring" aria-pressed="false"><span aria-hidden="true">💡</span>Inspiring</button>
        <button type="button" data-r="Let's talk" aria-pressed="false"><span aria-hidden="true">🤝</span>Let's talk</button>
        <button type="button" data-r="Coffee sometime?" aria-pressed="false"><span aria-hidden="true">☕</span>Coffee?</button>
      </div>
      <div class="react-note">
        <label class="sr-only" for="reactMsg">Optional note</label>
        <input id="reactMsg" name="message" maxlength="400" placeholder="Add a note or your email (optional)">
        <button class="send" id="reactSend" type="submit" disabled>Send</button>
      </div>
      <p class="react-status" id="reactStatus" role="status" aria-live="polite"></p>
    </form>

"""
anchor = '    <div class="tblock" role="contentinfo">'
assert anchor in html
html = html.replace(anchor, markup + anchor, 1)

js = """
  // Reactions: posted to Netlify Forms, which emails them to Sisi
  var rf=document.getElementById('reactForm'), rv=document.getElementById('reactValue'), rs=document.getElementById('reactSend'), rst=document.getElementById('reactStatus');
  if(rf){
    var picks=rf.querySelectorAll('.react-row button');
    Array.prototype.forEach.call(picks, function(b){
      b.addEventListener('click', function(){
        Array.prototype.forEach.call(picks, function(o){ o.setAttribute('aria-pressed', o===b ? 'true':'false'); });
        rv.value=b.getAttribute('data-r'); rs.disabled=false; rst.className='react-status'; rst.textContent='Ready to send "'+rv.value+'".';
      });
    });
    rf.addEventListener('submit', function(e){
      e.preventDefault();
      if(!rv.value) return;
      rs.disabled=true; rst.className='react-status'; rst.textContent='Sending…';
      var body=new URLSearchParams(new FormData(rf)).toString();
      fetch('/', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:body})
        .then(function(r){ if(!r.ok) throw new Error(r.status);
          rst.className='react-status ok'; rst.textContent='Sent. Thank you!';
          Array.prototype.forEach.call(picks, function(o){ o.setAttribute('aria-pressed','false'); });
          rv.value=''; document.getElementById('reactMsg').value='';
        })
        .catch(function(){ rs.disabled=false; rst.className='react-status err'; rst.textContent='That didn\\u2019t go through. Try again, or email me directly.'; });
    });
  }
"""
html = html.replace("  // Live Brooklyn time", js + "\n  // Live Brooklyn time", 1)

# --- split into a real document: title/meta/links/style go in <head> ---
cut = html.index("</style>") + len("</style>")
head_part, body_part = html[:cut], html[cut:]
reset = """<style>
:root{padding-top:env(safe-area-inset-top,0px); padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0; font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
img,video{max-width:100%}
[hidden]{display:none!important}
</style>"""
meta = """<meta property="og:title" content="Sisi Yu — Designer &amp; Technologist">
<meta property="og:description" content="Product case studies, physical computing, and research on AI trust, ethics and creativity.">
<meta property="og:type" content="website">
<meta property="og:image" content="jacket/lit.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.svg" type="image/svg+xml">"""
doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + reset + "\n" + head_part + "\n" + meta + "\n</head>\n<body>\n" + body_part.lstrip("\n") + "\n</body>\n</html>\n")
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(doc)

# --- favicon (images, videos and PDFs live in site/ and are committed directly) ---
open(os.path.join(out,"favicon.svg"),"w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#2B3BF0"/><path d="M8 9l3-5 4 5h2l4-5 3 5v12H8z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="miter"/><rect x="11" y="12" width="3" height="3" fill="#fff"/><rect x="18" y="12" width="3" height="3" fill="#fff"/><circle cx="25" cy="25" r="3" fill="#FF5A1F"/></svg>')
print("built site/index.html")
