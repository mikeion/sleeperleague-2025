import { getStore } from '@netlify/blobs';

export default async (req, context) => {
    try {
        // Get data from Netlify Blobs using context
        const store = getStore({
            name: 'fantasy-stats',
            siteID: context.site?.id,
            token: context.token
        });
        const data = await store.get('h2h-data');

        if (!data) {
            return new Response(JSON.stringify({ error: 'No H2H data found' }), {
                status: 404,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        return new Response(data, {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'public, max-age=3600' // Cache for 1 hour
            }
        });
    } catch (error) {
        console.error('Error retrieving H2H data:', error);
        return new Response(JSON.stringify({ error: error.message }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
};

export const config = {
    path: '/api/h2h'
};
