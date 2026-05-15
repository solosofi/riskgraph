const API = window.location.origin;
async function analyze() {
  const pkg = document.getElementById("pkg").value.trim();
  const eco = document.getElementById("ecosystem").value;
  if (!pkg) return;
  document.getElementById("result").style.display = "block";
  try {
    const r = await fetch(API+"/api/v1/package-risk/"+eco+"/"+pkg);
    const d = await r.json();
    document.getElementById("score").textContent = d.score.toFixed(1);
    const lvl = document.getElementById("level");
    lvl.textContent = d.level; lvl.className = "level " + d.level;
    let sigs = (d.signals||[]).map(s=>"\u26a0 "+s.name+": "+s.detail.slice(0,80)).join("<br>");
    document.getElementById("signals").innerHTML = sigs || "No risk signals.";
  } catch(e) {
    document.getElementById("score").textContent = "ERR";
    document.getElementById("signals").textContent = "Connection: " + e.message;
  }
}
