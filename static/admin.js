let currentPage = 1;
const perPage = 10;

async function fetchData(page = 1) {
    currentPage = page;
    const response = await fetch(`/admin/data?page=${page}&per_page=${perPage}`);
    const data = await response.json();
    const tbody = document.getElementById('data-table').querySelector('tbody');
    tbody.innerHTML = '';

    data.forEach(row => {
        const tr = document.createElement('tr');

        ['id', 'role', 'content', 'session_id', 'session_name'].forEach(key => {
            const td = document.createElement('td');
            td.textContent = row[key];
            if (key === 'content') {
                td.title = row[key]; // Add full content as title for overflow
                td.style.maxWidth = '200px'; // Limit width
                td.style.overflow = 'hidden';
                td.style.textOverflow = 'ellipsis';
                td.style.whiteSpace = 'nowrap';
            }
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });
    updatePagination();
}

function updatePagination() {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';

    const prevPage = document.createElement('button');
    prevPage.textContent = 'Previous';
    prevPage.disabled = currentPage === 1;
    prevPage.addEventListener('click', () => fetchData(currentPage - 1));
    pagination.appendChild(prevPage);

    const nextPage = document.createElement('button');
    nextPage.textContent = 'Next';
    nextPage.addEventListener('click', () => fetchData(currentPage + 1));
    pagination.appendChild(nextPage);
}

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});
