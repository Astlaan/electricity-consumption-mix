import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { mdsvex } from 'mdsvex';
import remarkMath from 'remark-math';
import rehypeKatexSvelte from 'rehype-katex-svelte';

const config = {
    extensions: ['.svelte', '.md'],
    preprocess: [
        vitePreprocess(),
        mdsvex({
            extensions: ['.md'],
            remarkPlugins: [remarkMath],
            rehypePlugins: [rehypeKatexSvelte],
        })
    ],
    kit: {
        adapter: adapter()
    }
};

export default config;