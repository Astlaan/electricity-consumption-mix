<svelte:head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />

    <!-- Favicon (.ico, 32x32) -->
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />

    <!-- Open Graph / Social Media Meta Tags -->
    <meta property="og:title" content="Portugal Electricity Consumption Mix" />
    <meta property="og:description" content="Portugal's electricity consumption taking imports into account." />
    <meta property="og:image" content="https://portugal-electricity-mix.vercel.app/og-image.jpg" />
    <!-- 1200x630, jpg or png -->
    <meta property="og:url" content="https://portugal-electricity-mix.vercel.app" />
    <meta property="og:type" content="website" />

    <!-- SEO -->
    <link rel="alternate" hreflang="en" href="https://portugal-electricity-mix.vercel.app/" />
    <link rel="alternate" hreflang="pt" href="https://portugal-electricity-mix.vercel.app/" />

    <meta name="description"
        content="Portugal's electricity consumption, including imports. Consumo de eletricidade em Portugal: mix elétrico, energia elétrica e contribuições das importações." />

    <!-- Validation -->
    <meta name="google-site-verification" content="gT-Wvv_yWs2-IV3ZnDhnjYsK31nyTMvbrF34_Tb1yzE" />
    <meta name="msvalidate.01" content="B9750948FEDB6C5AB8EB0E4A736E5420" />

    <!-- Packages -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

    <title>Portugal Electricity Consumption Mix</title>

    <!-- Add the Temml stylesheet here -->
    <link
      rel="stylesheet"
      href=" https://cdn.jsdelivr.net/npm/temml@0.11.6/dist/Temml-Local.min.css "
    />
</svelte:head>

<script lang="ts">
    import Header from "$lib/components/Header.svelte";
</script>

<Header />

<main>
    <slot />
</main>

<!-- Placeholder for Footer component -->
<div id="footer-placeholder"></div>

<style>
    :global(body) { /* Use :global for body styles or import a global CSS file */
        font-family: Arial, sans-serif;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    /* Styles that were previously directly in public/index.html */
    /* Consider moving these to a global.css if they grow too large */
    :global(.form-container) {
        margin-bottom: 20px;
        padding: 20px;
        background-color: #f5f5f5;
        border-radius: 5px;
    }

    :global(.error-message) {
        color: #721c24;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        padding: 10px;
        margin: 10px 0;
        display: none; /* Will be controlled by Svelte state */
    }

    :global(.error-item) {
        margin: 5px 0;
    }

    :global(.loading) {
        /* display: none; Will be controlled by Svelte state */
        margin-top: 10px;
        color: #666;
    }

    :global(button) {
        padding: 10px 20px;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }

    :global(button:disabled) {
        background-color: #cccccc;
        cursor: not-allowed;
    }

    :global(input[type="datetime-local"]) {
        padding: 5px;
        margin-right: 10px;
    }

    :global(#plotContainer) { /* This ID might be specific to the page, not layout */
        width: 100%;
        height: 90vh;
        margin: 20px 0;
    }

    :global(.plot-container.plotly) { /* This class might be specific to the page */
        justify-items: center;
    }

    :global(.time-field) {
        margin: 10px 0;
    }

    :global(.help-text) {
        font-size: 0.8em;
        color: #666;
    }

    :global(.inline-help-text) {
        font-size: 0.8em;
        color: #666;
        display: inline;
        margin-left: 5px;
        cursor: help;
        position: relative;
    }

    :global(.inline-help-text:hover::after) {
        content: "Hovering over the plot will show all details.";
        position: absolute;
        background-color: #333;
        color: #fff;
        padding: 5px 10px;
        border-radius: 4px;
        white-space: nowrap;
        left: 50%;
        transform: translateX(-50%);
        bottom: 125%;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s;
        z-index: 1000;
    }

    :global(.inline-help-text:hover::after) {
        opacity: 1;
        visibility: visible;
    }

    :global(input[name="timeMode"]:disabled+label) {
        color: #cccccc;
        cursor: not-allowed;
    }

    :global(.mode-selector) {
        margin-bottom: 20px;
    }

    :global(#advancedControls .time-field input) { /* This ID might be specific to the page */
        width: 300px;
        padding: 5px;
    }

    :global(.plot-type-selector) { /* This class might be specific to the page */
        margin-bottom: 20px;
        padding: 10px;
        background-color: #fff;
        border-radius: 4px;
    }

    :global(.plot-type-selector label) { /* This class might be specific to the page */
        margin-right: 15px;
    }
</style>
