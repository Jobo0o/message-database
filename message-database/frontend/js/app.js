document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.getElementById('messages-container');
    const singleMessageContainer = document.getElementById('singleMessageContainer');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const currentPageSpan = document.getElementById('currentPage');
    const messageIdInput = document.getElementById('messageIdInput');
    const fetchByIdButton = document.getElementById('fetchByIdButton');

    // --- Configuration ---
    // Note: Ensure the backend FastAPI application (API V2) is running.
    // By default, this script assumes the API is available at http://localhost:8000/api_v2
    // If your API is running on a different port or path, update API_BASE_URL.
    const API_BASE_URL = 'http://localhost:8000/api_v2'; // Corrected to match provided path
    const LIMIT = 10;
    let currentPage = 1;
    let currentSkip = 0;

    // --- Helper Functions ---
    function displayError(container, message) {
        container.innerHTML = `<p class="error" style="color: red;">Error: ${message}</p>`;
    }

    function renderMessage(message) {
        return `
            <div class="message">
                <p><strong>ID:</strong> ${message.message_id}</p>
                <p><strong>Content:</strong> ${message.content}</p>
                <p><strong>Guest:</strong> ${message.guest.name}</p>
                <p><strong>Property:</strong> ${message.property.name}</p>
                <p><strong>Timestamp:</strong> ${new Date(message.timestamp).toLocaleString()}</p>
                <p><strong>Direction:</strong> ${message.direction}</p>
                <p><strong>Type:</strong> ${message.message_type}</p>
            </div>
        `;
    }

    // --- API Fetching ---
    async function fetchMessages(skip = 0, limit = LIMIT) {
        messagesContainer.innerHTML = '<p>Loading messages...</p>';
        try {
            const response = await fetch(`${API_BASE_URL}/messages?skip=${skip}&limit=${limit}`);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            const messages = await response.json();

            messagesContainer.innerHTML = ''; // Clear loading/previous messages
            if (messages.length === 0) {
                messagesContainer.innerHTML = '<p>No messages found.</p>';
            } else {
                messages.forEach(message => {
                    messagesContainer.innerHTML += renderMessage(message);
                });
            }
            updatePaginationControls(messages.length);
        } catch (error) {
            console.error('Failed to fetch messages:', error);
            displayError(messagesContainer, error.message);
        }
    }

    async function fetchMessageById(messageId) {
        singleMessageContainer.innerHTML = '<p>Loading message...</p>';
        if (!messageId) {
            displayError(singleMessageContainer, 'Please enter a Message ID.');
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/messages/${messageId}`);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            const message = await response.json();
            singleMessageContainer.innerHTML = renderMessage(message);
        } catch (error) {
            console.error('Failed to fetch message by ID:', error);
            displayError(singleMessageContainer, error.message);
        }
    }

    // --- Pagination ---
    function updatePaginationControls(fetchedCount) {
        currentPageSpan.textContent = `Page: ${currentPage}`;
        prevButton.disabled = currentSkip === 0;
        nextButton.disabled = fetchedCount < LIMIT; // Disable next if fewer than limit items were fetched
    }

    prevButton.addEventListener('click', () => {
        if (currentSkip > 0) {
            currentSkip -= LIMIT;
            currentPage--;
            fetchMessages(currentSkip);
        }
    });

    nextButton.addEventListener('click', () => {
        currentSkip += LIMIT;
        currentPage++;
        fetchMessages(currentSkip);
    });

    // --- Fetch by ID ---
    fetchByIdButton.addEventListener('click', () => {
        const messageId = messageIdInput.value.trim();
        fetchMessageById(messageId);
    });

    // --- Initial Load ---
    fetchMessages(currentSkip);
});
