async function fetchData() {
    const response = await fetch('/admin/data');
    const data = await response.json();
    const tbody = document.getElementById('data-table').querySelector('tbody');
    tbody.innerHTML = '';
    data.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach(cell => {
            const td = document.createElement('td');
            td.textContent = cell;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

fetchData();
