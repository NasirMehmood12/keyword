const apiBase = "http://localhost:5000"; // Change if hosted elsewhere

async function loadKeywords() {
  const date = document.getElementById("datePicker").value;
  if (!date) return alert("Please select a date.");

  const response = await fetch(`${apiBase}/keywords/${date}`);
  const data = await response.json();

  const container = document.getElementById("mainKeywords");
  container.innerHTML = "";

  if (data.keywords.length === 0) {
    container.innerHTML = "No keywords found for this date.";
    return;
  }

  data.keywords.forEach(kw => {
    const div = document.createElement("div");
    div.className = "cloud";
    div.innerText = kw;
    div.onclick = () => showStructure(date, kw);
    container.appendChild(div);
  });
}

async function showStructure(date, keyword) {
  const response = await fetch(`${apiBase}/clouds/${date}/${encodeURIComponent(keyword)}`);
  const data = await response.json();

  const structure = document.getElementById("keywordStructure");
  structure.innerHTML = "";

  const main = document.createElement("div");
  main.className = "cloud";
  main.innerText = keyword;

  const link1 = document.createElement("div");
  link1.className = "link-line";

  const middle = document.createElement("div");
  middle.className = "cloud-block";
  middle.appendChild(main);
  middle.appendChild(link1);

  const primaryGroup = document.createElement("div");
  primaryGroup.className = "cloud-block";
  primaryGroup.innerHTML = `<div><strong>Primary</strong></div>`;
  data.primary.forEach(p => {
    const cloud = document.createElement("div");
    cloud.className = "cloud";
    cloud.innerText = p;
    primaryGroup.appendChild(cloud);
  });

  const secondaryGroup = document.createElement("div");
  secondaryGroup.className = "cloud-block";
  secondaryGroup.innerHTML = `<div><strong>Secondary</strong></div>`;
  data.secondary.forEach(s => {
    const cloud = document.createElement("div");
    cloud.className = "cloud";
    cloud.innerText = s;
    secondaryGroup.appendChild(cloud);
  });

  structure.appendChild(middle);
  structure.appendChild(primaryGroup);
  structure.appendChild(secondaryGroup);
}
