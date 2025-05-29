import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { mdsvex } from 'mdsvex';
import { mathsvex } from 'mathsvex';
import remarkMath from 'remark-math';
import rehypeKatexSvelte from 'rehype-katex-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// extensions: ['.svelte', '.md'], // mdsvex
	extensions: ['.svelte', '.md', '.math.js', '.math.ts'], // mathsvex

	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: [
		vitePreprocess(),
		mathsvex(),
		// mdsvex({
		// 	extensions: ['.md', '.svx'], // Tell mdsvex to only process .md files
		// 	highlight: {
		// 		// highlighter: customHighlighter, // You can add a syntax highlighter here if needed
		// 	},
		// 	// Configure remark and rehype plugins for math/KaTeX
		// 	remarkPlugins: [remarkMath],
		// 	rehypePlugins: [rehypeKatexSvelte],
		// 	// You can pass KaTeX options here if needed, e.g., displayMode: true for block equations
		// 	// katex: {
		// 	//   // See https://katex.org/docs/options.html
		// 	// }
		// })
	],

	kit: {
		// adapter-auto only supports some environments, see https://svelte.dev/docs/kit/adapter-auto for a list.
		// If your environment is not supported, or you settled on a specific environment, switch out the adapter.
		// See https://svelte.dev/docs/kit/adapters for more information about adapters.
		adapter: adapter()
	}
};

export default config;
