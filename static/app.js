document.addEventListener("DOMContentLoaded", () => {
    checkStatus();
    loadDocumentsList();
});

function switchTab(tabName) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

    document.getElementById(`tab-${tabName}`).classList.add("active");
    document.getElementById(`tab-${tabName}-btn`).classList.add("active");
}

async function checkStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const badge = document.getElementById("backend-status");
        if (data.supabase_connected) {
            badge.innerHTML = `<span class="status-dot"></span> Backend Conectado | Supabase OK (${data.embedding_model})`;
        } else {
            badge.innerHTML = `<span class="status-dot" style="background:#EF4444"></span> Erro de Conexão Supabase`;
        }
    } catch (err) {
        console.error("Failed status check:", err);
    }
}

async function loadDocumentsList() {
    try {
        const res = await fetch("/api/documents");
        const data = await res.json();
        const container = document.getElementById("doc-checkboxes");
        container.innerHTML = "";

        if (!data.documents || data.documents.length === 0) {
            container.innerHTML = "<p>Nenhum documento PDF encontrado.</p>";
            return;
        }

        data.documents.forEach(doc => {
            const label = document.createElement("label");
            label.className = "doc-checkbox-item";
            label.innerHTML = `
                <input type="checkbox" value="${doc}" checked>
                <span>${doc}</span>
            `;
            container.appendChild(label);
        });
    } catch (err) {
        console.error("Failed loading docs list:", err);
    }
}

async function startIngestion() {
    const checkboxes = document.querySelectorAll("#doc-checkboxes input[type='checkbox']:checked");
    const selectedFiles = Array.from(checkboxes).map(cb => cb.value);

    if (selectedFiles.length === 0) {
        alert("Selecione pelo menos um documento para ingestão.");
        return;
    }

    const btn = document.getElementById("btn-start-ingestion");
    btn.disabled = true;
    btn.innerText = "Processando Ingestão...";

    // Reset stepper
    ["step-ing", "step-tok", "step-emb", "step-vec"].forEach(id => {
        document.getElementById(id).classList.add("active");
    });

    try {
        const res = await fetch("/api/ingest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ files: selectedFiles })
        });
        const data = await res.json();

        if (data.success) {
            // Render logs
            const logsCard = document.getElementById("ingestion-logs-card");
            logsCard.style.display = "block";
            const logContainer = document.getElementById("ingestion-log-details");
            logContainer.innerHTML = "";

            data.steps.forEach(st => {
                const div = document.createElement("div");
                div.className = "log-item";
                div.innerHTML = `<span class="log-step-name">[${st.step}]:</span> ${st.detail}`;
                logContainer.appendChild(div);
            });

            // Render tabular structured data
            if (data.tabular_data && data.tabular_data.length > 0) {
                const tabCard = document.getElementById("tabular-data-card");
                tabCard.style.display = "block";
                const tbody = document.getElementById("tabular-table-body");
                tbody.innerHTML = "";

                data.tabular_data.forEach(row => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>${row.documento}</strong></td>
                        <td>${row.nota_fiscal || '-'}</td>
                        <td>${row.data || '-'}</td>
                        <td>${row.emitente || '-'}</td>
                        <td>${row.destinatario || '-'}</td>
                        <td><strong>${row.valor_total || '-'}</strong></td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            ["step-ing", "step-tok", "step-emb", "step-vec"].forEach(id => {
                document.getElementById(id).classList.remove("active");
                document.getElementById(id).classList.add("completed");
            });

        } else {
            alert("Falha na ingestão: " + (data.error || "Erro desconhecido"));
        }
    } catch (err) {
        alert("Erro de comunicação: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerText = "Iniciar Ingestão e Processamento RAG";
    }
}

function handleKeyPress(e) {
    if (e.key === "Enter") {
        sendQuery();
    }
}

function setQuery(qText) {
    document.getElementById("query-input").value = qText;
    sendQuery();
}

async function sendQuery() {
    const input = document.getElementById("query-input");
    const qText = input.value.trim();

    if (!qText) {
        alert("Digite uma pergunta.");
        return;
    }

    const btn = document.getElementById("btn-send-query");
    btn.disabled = true;
    btn.innerText = "Buscando...";

    // Stepper highlight
    for (let i = 1; i <= 6; i++) {
        document.getElementById(`qstep-${i}`).classList.add("active");
    }

    try {
        const res = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: qText })
        });
        const data = await res.json();

        // Render Final Answer
        const answerCard = document.getElementById("answer-card");
        answerCard.style.display = "block";
        const answerBody = document.getElementById("final-answer-text");
        answerBody.innerText = data.final_response || "Sem dados disponíveis na base";

        // Render Top 5 Retrieval Candidates
        const retContainer = document.getElementById("retrieval-results-list");
        retContainer.innerHTML = "";

        if (data.candidates && data.candidates.length > 0) {
            data.candidates.forEach((cand, i) => {
                const item = document.createElement("div");
                item.className = "retrieval-item";
                item.innerHTML = `
                    <div class="retrieval-header">
                        <span class="doc-name">Resultado ${i+1}: ${cand.document_name}</span>
                        <span class="score-tag">Score: ${cand.score}</span>
                    </div>
                    <div class="retrieval-text">${cand.content}</div>
                `;
                retContainer.appendChild(item);
            });
        } else {
            retContainer.innerHTML = `<div class="empty-state">Sem dados disponíveis na base</div>`;
        }

        // Render Augmented Prompt
        if (data.augmented_prompt) {
            const promptCard = document.getElementById("prompt-card");
            promptCard.style.display = "block";
            document.getElementById("augmented-prompt-text").innerText = data.augmented_prompt;
        }

    } catch (err) {
        alert("Erro durante a consulta: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerText = "Enviar";
        for (let i = 1; i <= 6; i++) {
            document.getElementById(`qstep-${i}`).classList.remove("active");
        }
    }
}
