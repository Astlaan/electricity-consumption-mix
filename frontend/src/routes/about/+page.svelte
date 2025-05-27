<script lang="ts">
    import { onMount } from 'svelte';

    // Forward declare Marked and KaTeX renderMathInElement
    declare let marked: any;
    declare let renderMathInElement: any;

    let contentHtml = '';
    let isLoading = true;
    let errorMessage = '';

    onMount(async () => {
        try {
            const response = await fetch('/content/about.md'); // Path relative to static dir
            if (!response.ok) {
                throw new Error(`Failed to fetch about.md: ${response.statusText}`);
            }
            const markdown = await response.text();
            
            if (typeof marked !== 'undefined') {
                contentHtml = marked.parse(markdown);
            } else {
                throw new Error('Marked.js library not loaded.');
            }

            // Wait for the DOM to update with contentHtml
            await tick(); 

            if (typeof renderMathInElement !== 'undefined') {
                console.log("Attempting to render KaTeX math...");
                // Try rendering on the whole document body, similar to the original script's approach
                // This can sometimes be more robust for dynamically inserted content.
                renderMathInElement(document.body, {
                    delimiters: [
                        { left: "$$", right: "$$", display: true },
                        { left: "$", right: "$", display: false }
                    ],
                    // Optional: specify elements to ignore if rendering on document.body
                    // ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
                    // errorCallback: (err) => console.error("KaTeX Error:", err) 
                });
                console.log("KaTeX rendering attempted on document.body.");
            } else {
                console.warn('KaTeX renderMathInElement not loaded. Math will not be rendered.');
            }
        } catch (error: any) {
            errorMessage = error.message;
            console.error("Error loading or rendering about page content:", error);
        } finally {
            isLoading = false;
        }
    });

    // Svelte's tick function to wait for DOM updates
    import { tick } from 'svelte';

</script>

<svelte:head>
    <title>About - Portugal Electricity Consumption Mix</title>
    <!-- Favicon is in global layout -->
    
    <!-- Add marked library for markdown -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js" defer></script>
    
    <!-- KATEX -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" crossorigin="anonymous" />
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js" crossorigin="anonymous" defer></script>
    <!-- auto-render is usually called after DOM is ready, so deferring it or calling manually -->
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" crossorigin="anonymous" defer></script>
</svelte:head>

<div class="content-container">
    {#if isLoading}
        <p>Loading content...</p>
    {:else if errorMessage}
        <p style="color: red;">Error: {errorMessage}</p>
    {:else}
        <div id="markdown-content">
            {@html contentHtml}
        </div>
    {/if}
</div>

<style>
    /* Styles from public/about/index.html */
    .content-container { /* Renamed from .content to avoid conflict if layout has .content */
        line-height: 1.6;
    }

    :global(.content-container img) { /* Use :global if markdown content is outside component scope */
        max-width: 100%;
        height: auto;
    }

    :global(.content-container code) {
        background-color: #f5f5f5;
        padding: 2px 4px;
        border-radius: 4px;
    }

    :global(.content-container pre) {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 4px;
        overflow-x: auto;
    }

    /* Body styles are in global layout */
</style>
