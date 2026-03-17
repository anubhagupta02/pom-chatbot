
async function submitQuery() {
    const query = document.getElementById('queryInput').value.trim();
    console.log("Query submitted:", query);
    if (!query) return;

    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    try {
        console.log("Sending request to /query");
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        console.log("Response status:", response.status, "OK:", response.ok);
        const data = await response.json();
        console.log("Response data received:", data);

        if (response.ok) {
            console.log("Success! Calling displayResults");
            displayResults(data);
        } else {
            console.log("API error - Status:", response.status, "Error:", data.error);
            showError("Error (Status " + response.status + "): " + JSON.stringify(data.error));
        }
    } catch (error) {
        console.log("Catch error:", error.message);
        showError('Network error: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function displayResults(data) {
    console.log("=== displayResults called ===");
    console.log("Full data object:", data);
    console.log("data.data:", data.data);
    console.log("data.sql:", data.sql);
    // Display SQL
    document.getElementById('sqlDisplay').textContent = data.sql;

    // Display table
    const tableData = data.data.data;
    console.log("tableData in index.html: ", tableData);
    if (Array.isArray(tableData) && tableData.length > 0) {
        const headers = Object.keys(tableData[0]);
        const head = document.getElementById('tableHead');
        const body = document.getElementById('tableBody');

        // Clear previous content
        head.innerHTML = '';
        body.innerHTML = '';

        // Create header
        const headerRow = document.createElement('tr');
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        head.appendChild(headerRow);

        // Create rows
        tableData.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = row[header] || '';
                tr.appendChild(td);
            });
            body.appendChild(tr);
        });
    } else {
        document.getElementById('tableBody').innerHTML = '<tr><td colspan="100%">No data returned</td></tr>';
    }

    document.getElementById('results').style.display = 'block';
}

function showError(message) {
    console.log("=== ERROR ===", message);
    document.getElementById('error').textContent = message;
    document.getElementById('error').style.display = 'block';
}

// Allow Enter key to submit
document.getElementById('queryInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        submitQuery();
    }
});
