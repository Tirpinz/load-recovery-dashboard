let incidents = JSON.parse(localStorage.getItem('loadRecoveryIncidents')) || [];

// Show/Hide Sections
function showSection(section) {
  document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
  document.getElementById(section + '-section').style.display = 'block';
  
  if (section === 'dashboard') updateDashboard();
  if (section === 'incidents') renderIncidentsTable();
}

// Form Submit
document.getElementById('incident-form').addEventListener('submit', function(e) {
  e.preventDefault();
  
  const newIncident = {
    date: new Date().toLocaleDateString(),
    truck: document.getElementById('truck-id').value,
    trailer: document.getElementById('trailer-id').value,
    load: document.getElementById('load-id').value,
    alertTime: document.getElementById('alert-time').value,
    type: document.getElementById('incident-type').value,
    resolution: document.getElementById('resolution-method').value,
    cost: parseFloat(document.getElementById('recovery-cost').value) || 0,
    success: document.getElementById('success-yn').value,
    notes: document.getElementById('notes').value
  };
  
  // Simple MTTR calculation (you can improve later)
  newIncident.mttr = (Math.random() * 5 + 2).toFixed(2); // placeholder
  
  incidents.push(newIncident);
  localStorage.setItem('loadRecoveryIncidents', JSON.stringify(incidents));
  
  alert('Incident logged successfully!');
  this.reset();
  showSection('dashboard');
});

// Update KPI Dashboard
function updateDashboard() {
  const total = incidents.length;
  const successCount = incidents.filter(i => i.success === 'Y').length;
  const successRate = total ? ((successCount / total) * 100).toFixed(0) : 0;
  const avgCost = total ? (incidents.reduce((sum, i) => sum + i.cost, 0) / total).toFixed(0) : 0;
  const avgMTTR = total ? (incidents.reduce((sum, i) => sum + parseFloat(i.mttr || 0), 0) / total).toFixed(1) : 0;

  document.getElementById('total-incidents').querySelector('span').textContent = total;
  document.getElementById('mttr').querySelector('span').textContent = avgMTTR;
  document.getElementById('success-rate').querySelector('span').textContent = successRate + '%';
  document.getElementById('avg-cost').querySelector('span').textContent = avgCost;

  // Render Charts (simple versions)
  renderCharts();
}

function renderCharts() {
  // You can expand these with real Chart.js logic
  console.log('Charts would render here with your data');
  // Add full Chart.js code if you want — I can expand this in the next step.
}

// Render Incidents Table
function renderIncidentsTable() {
  const tbody = document.querySelector('#incidents-table tbody');
  tbody.innerHTML = '';
  
  incidents.forEach(inc => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${inc.date}</td>
      <td>${inc.truck}</td>
      <td>${inc.trailer}</td>
      <td>${inc.load}</td>
      <td>${inc.type}</td>
      <td>${inc.mttr}</td>
      <td>${inc.success}</td>
    `;
    tbody.appendChild(row);
  });
}

// Theme Toggle
function toggleTheme() {
  document.body.classList.toggle('dark-mode');
}

// Initial Load
showSection('dashboard');