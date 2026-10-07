let newsData = [];
let selectedIndex = 0;
let isReading = false;

const newsListEl = document.getElementById('newsList');
const newsReaderEl = document.getElementById('newsReader');
const listControlsEl = document.getElementById('listControls');
const readerTitleEl = document.getElementById('readerTitle');
const readerContentEl = document.getElementById('readerContent');
const readerSourceEl = document.getElementById('readerSource');
const statusMessageEl = document.getElementById('statusMessage');

async function fetchNews() {
    newsListEl.innerHTML = '<li class="news-item" style="border: none;">[SYSTEM] Fetching data stream...<span class="blink">_</span></li>';
    try {
        const response = await fetch('/api/bulletin/fetch');
        const result = await response.json();
        
        if (result.status === 'success' && result.articles && result.articles.length > 0) {
            newsData = result.articles;
            renderList();
        } else {
            newsListEl.innerHTML = `<li class="news-item" style="border: none; color: red;">[ERROR] ${result.message || 'No data found'}</li>`;
        }
    } catch (error) {
        newsListEl.innerHTML = `<li class="news-item" style="border: none; color: red;">[FATAL] Connection lost. ${error.message}</li>`;
    }
}

function renderList() {
    newsListEl.innerHTML = '';
    newsData.forEach((news, index) => {
        const li = document.createElement('li');
        li.className = `news-item ${index === selectedIndex ? 'selected' : ''}`;
        li.innerHTML = `
            <div>> ${news.title}</div>
            <div class="source">[SOURCE: ${news.source}]</div>
        `;
        li.onclick = () => {
            if (!isReading) {
                selectedIndex = index;
                renderList();
                openReader();
            }
        };
        newsListEl.appendChild(li);
    });

    // Ensure selected item is visible
    const selectedEl = document.querySelector('.news-item.selected');
    if (selectedEl) {
        selectedEl.scrollIntoView({ block: 'nearest' });
    }
}

let currentTypewriterTimeout = null;

function typeWriter(text, element, speed = 8) {
    if (currentTypewriterTimeout) {
        clearTimeout(currentTypewriterTimeout);
        currentTypewriterTimeout = null;
    }
    element.textContent = '';
    let i = 0;
    const len = text.length;
    // Chunk typing for long articles to keep it responsive
    const chunkSize = len > 500 ? 3 : 1;
    function type() {
        if (i < len) {
            element.textContent += text.substring(i, i + chunkSize);
            i += chunkSize;
            currentTypewriterTimeout = setTimeout(type, speed);
        } else {
            currentTypewriterTimeout = null;
        }
    }
    type();
}

function openReader() {
    if (newsData.length === 0) return;
    const news = newsData[selectedIndex];
    
    isReading = true;
    newsListEl.style.display = 'none';
    listControlsEl.style.display = 'none';
    newsReaderEl.classList.add('active');
    
    readerTitleEl.textContent = `> ${news.title}`;
    readerSourceEl.textContent = `[SOURCE: ${news.source}]`;
    typeWriter(news.content || "No content available.", readerContentEl, 8);
}

function closeReader() {
    if (currentTypewriterTimeout) {
        clearTimeout(currentTypewriterTimeout);
        currentTypewriterTimeout = null;
    }
    isReading = false;
    newsReaderEl.classList.remove('active');
    newsListEl.style.display = '';
    listControlsEl.style.display = '';
    readerContentEl.textContent = '';
    renderList();
}

async function markCurrentNews() {
    if (newsData.length === 0) return;
    const news = newsData[selectedIndex];
    
    showStatus("SAVING TO DATASET...");
    
    try {
        const response = await fetch('/api/bulletin/mark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(news)
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            showStatus("SUCCESS: DATA MARKED FOR FINE-TUNING");
        } else {
            showStatus("ERROR: " + result.message);
        }
    } catch (error) {
        showStatus("FATAL: UNABLE TO SAVE DATA");
    }
}

function showStatus(msg) {
    statusMessageEl.innerText = msg;
    statusMessageEl.style.display = 'block';
    setTimeout(() => {
        statusMessageEl.style.display = 'none';
    }, 3000);
}

document.addEventListener('keydown', (e) => {
    if (isReading) {
        if (e.key === 'Escape') {
            closeReader();
        } else if (e.key.toLowerCase() === 'm') {
            markCurrentNews();
        }
    } else {
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (selectedIndex > 0) {
                selectedIndex--;
                renderList();
            }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (selectedIndex < newsData.length - 1) {
                selectedIndex++;
                renderList();
            }
        } else if (e.key === 'Enter') {
            openReader();
        } else if (e.key.toLowerCase() === 'm') {
            markCurrentNews();
        }
    }
});

// Initialize
setTimeout(fetchNews, 1000);
