import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { mdsvex } from 'mdsvex';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	extensions: ['.svelte', '.md'], // Add .md extension

	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: [
		vitePreprocess(),
		mdsvex({
			extensions: ['.md'], // Tell mdsvex to only process .md files
			highlight: {
				// highlighter: customHighlighter, // You can add a syntax highlighter here if needed
			},
			// KaTeX configuration for LaTeX
			// mdsvex has built-in support for KaTeX if remark-math and rehype-katex are not used explicitly
			// Ensure katex is installed: pnpm add -D katex
			// You might need to pass options to KaTeX if default behavior isn't sufficient
			// For example:
			// remarkPlugins: [], // Add remark plugins here
			// rehypePlugins: [], // Add rehype plugins here
			// katex: {
			//   // KaTeX options, e.g., displayMode: true for block equations
			//   // See https://katex.org/docs/options.html
			// }
			// If remark-math and rehype-katex were intended, they would be configured here.
			// Since they were removed, relying on mdsvex's direct or default KaTeX handling.
		})
	],

	kit: {
		// adapter-auto only supports some environments, see https://svelte.dev/docs/kit/adapter-auto for a list.
		// If your environment is not supported, or you settled on a specific environment, switch out the adapter.
		// See https://svelte.dev/docs/kit/adapters for more information about adapters.
		adapter: adapter()
	}
};

export default config;
