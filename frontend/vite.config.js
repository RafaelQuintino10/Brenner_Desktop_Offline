// // import { defineConfig } from 'vite'
// // import react from '@vitejs/plugin-react'
// // export default defineConfig({
// //   plugins:[react()],
// //   server:{host:'0.0.0.0',port:5173},
// // })



// import { defineConfig } from 'vite';
// import react from '@vitejs/plugin-react';
// import { fileURLToPath } from 'node:url';

// export default defineConfig({
//   plugins: [react()],

//   server: {
//     port: 5173,
//     host: '0.0.0.0',
//   },

//   build: {
//     rollupOptions: {
//       input: {
//         landing: fileURLToPath(
//           new URL('./index.html', import.meta.url)
//         ),
//         admin: fileURLToPath(
//           new URL('./admin/index.html', import.meta.url)
//         ),
//       },
//     },
//   },
// });

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

// Corrige /admin para /admin/
function adminRedirect(req, res, next) {
  const url = new URL(req.url, 'http://localhost');

  // if (url.pathname === '/admin') {
  //   res.statusCode = 308;
  //   res.setHeader(
  //     'Location',
  //     `/admin/${url.search}`
  //   );
  //   res.end();
  //   return;
  // }
  if (
  url.pathname === '/admin' ||
  url.pathname === '/barbearia'
) {
  res.statusCode = 308;

  res.setHeader(
    'Location',
    `${url.pathname}/${url.search}`
  );

  res.end();
  return;
}

  next();
}

const adminRoutes = {
  name: 'admin-routes',

  configureServer(server) {
    server.middlewares.use(adminRedirect);
  },

  configurePreviewServer(server) {
    server.middlewares.use(adminRedirect);
  },
};

export default defineConfig({
  plugins: [
    react(),
    adminRoutes,
  ],

  server: {
    port: 5173,
    host: '0.0.0.0',
  },

  build: {
    rollupOptions: {
      // input: {
      //   landing: fileURLToPath(
      //     new URL('./index.html', import.meta.url)
      //   ),

      //   admin: fileURLToPath(
      //     new URL('./admin/index.html', import.meta.url)
      //   ),
      // },
      input: {
  landing: fileURLToPath(
    new URL('./index.html', import.meta.url)
  ),

  admin: fileURLToPath(
    new URL('./admin/index.html', import.meta.url)
  ),

  barbearia: fileURLToPath(
    new URL('./barbearia/index.html', import.meta.url)
  ),
},
    },
  },
});
