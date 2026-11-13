// Genera las imágenes de perfil y portadas de Boccocitos.
// Uso: node redes/src/render.js   (usa Playwright + Chromium)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SRC = __dirname;
const OUT = path.join(__dirname, '..');

const C = {
  terracota: '#C35F28', terracotaOsc: '#8F4219', verde: '#526832',
  dorado: '#E3A031', crema: '#F5ECDB', carbon: '#231F20',
};

const base = `
@font-face{font-family:"Roboto Slab";src:url(roboto-slab-var.woff2) format("woff2");font-weight:100 900}
@font-face{font-family:"Mulish";src:url(mulish-var.woff2) format("woff2");font-weight:200 1000}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Mulish,sans-serif;color:${C.carbon};overflow:hidden}
.slab{font-family:"Roboto Slab",serif}
.chips{display:flex;gap:.6em;flex-wrap:wrap}
.chips span{border-radius:999px;padding:.35em .9em;font-weight:800;white-space:nowrap}
`;

// Íconos de línea para las portadas de historias destacadas (trazo blanco)
const I = {
  productos: '<path d="M18 22h28l-3 32H21z"/><path d="M25 22v-4a7 7 0 0 1 14 0v4"/><circle cx="27" cy="38" r="3"/><circle cx="37" cy="44" r="3"/><circle cx="36" cy="33" r="2.5"/>',
  preparacion: '<rect x="16" y="14" width="32" height="40" rx="8"/><circle cx="32" cy="38" r="9"/><path d="M32 33v5l3 2"/><path d="M24 21h16"/>',
  comprar: '<path d="M32 56s-15-14.5-15-27a15 15 0 0 1 30 0c0 12.5-15 27-15 27z"/><circle cx="32" cy="29" r="5.5"/>',
  negocios: '<path d="M12 26h40l-4-10H16z"/><path d="M15 26v26h34V26"/><path d="M27 52V38h10v14"/><path d="M12 26a6.6 6.6 0 0 0 13.3 0 6.6 6.6 0 0 0 13.4 0 6.6 6.6 0 0 0 13.3 0"/>',
  nosotros: '<path d="M32 54V30"/><path d="M32 36c-10 0-15-7-15-16 10 0 15 7 15 16z"/><path d="M32 30c0-9 5-16 15-16 0 9-5 16-15 16z"/><path d="M20 54h24"/>',
  pedidos: '<path d="M14 50l3-10a19 19 0 1 1 7 7z"/><path d="M26 25c0 8 5 13 13 14l3-3-4-3-2 2c-3-1-5-3-6-6l2-2-3-4z"/>',
  recetas: '<path d="M14 34h36a18 18 0 0 1-36 0z"/><path d="M24 26c0-3 3-3 3-6s-3-3-3-6"/><path d="M33 26c0-3 3-3 3-6s-3-3-3-6"/><path d="M42 26c0-3 3-3 3-6s-3-3-3-6"/>',
};
const icon = (k, size, stroke = '#fff') =>
  `<svg width="${size}" height="${size}" viewBox="0 0 64 64" fill="none" stroke="${stroke}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">${I[k]}</svg>`;

const designs = [
  // ---------- FOTOS DE PERFIL ----------
  {
    file: 'perfil-principal.png', w: 1080, h: 1080,
    html: `<div style="width:1080px;height:1080px;background:${C.crema};display:grid;place-items:center">
      <img src="logo-boccos.svg" style="width:640px"></div>`,
  },
  {
    file: 'perfil-terracota.png', w: 1080, h: 1080,
    html: `<div style="width:1080px;height:1080px;background:${C.terracota};display:grid;place-items:center">
      <img src="logo-white.svg" style="width:640px"></div>`,
  },
  {
    file: 'perfil-icono.png', w: 1080, h: 1080,
    html: `<div style="width:1080px;height:1080px;background:${C.crema};display:grid;place-items:center">
      <img src="emblem.svg" style="height:700px;transform:translateY(-10px)"></div>`,
  },

  // ---------- FACEBOOK (1640x624; móvil recorta los lados) ----------
  {
    file: 'portada-facebook.png', w: 1640, h: 624,
    html: `<div style="position:relative;width:1640px;height:624px;background:${C.crema}">
      <img src="escena1.webp" style="position:absolute;right:0;top:0;height:624px;width:960px;object-fit:cover;object-position:40% 50%">
      <div style="position:absolute;right:0;top:0;width:960px;height:624px;background:linear-gradient(90deg,${C.crema} 0%,rgba(245,236,219,.0) 52%)"></div>
      <div style="position:absolute;left:200px;top:0;height:624px;width:860px;display:flex;flex-direction:column;justify-content:center;gap:26px">
        <div style="font-weight:900;letter-spacing:.14em;color:${C.terracota};font-size:22px">HECHO EN MANABÍ · DE LA FINCA A TU MESA</div>
        <div class="slab" style="font-weight:800;font-size:96px;line-height:.98;color:${C.carbon}">¡Sabor que<br>te abraza!</div>
        <div style="font-size:30px;font-weight:600;color:#4f4741;line-height:1.3">Mini bolones, muchines, pan de yuca y María Pipona:<br>del congelador a tu mesa en minutos.</div>
        <div class="chips" style="font-size:22px">
          <span style="background:${C.verde};color:#fff">Sin gluten</span>
          <span style="background:${C.terracota};color:#fff">Air fryer 13–15 min</span>
          <span style="background:${C.dorado};color:${C.carbon}">Supermercados de Manabí</span>
        </div>
      </div></div>`,
  },

  // ---------- YOUTUBE (2560x1440; zona segura central 1546x423) ----------
  {
    file: 'portada-youtube.png', w: 2560, h: 1440,
    html: `<div style="position:relative;width:2560px;height:1440px">
      <img src="escena1.webp" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 45%">
      <div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(35,31,32,.82) 0%,rgba(35,31,32,.55) 45%,rgba(35,31,32,.15) 75%)"></div>
      <div style="position:absolute;left:507px;top:508px;width:1546px;height:423px;display:flex;align-items:center;gap:60px">
        <img src="emblem-white.svg" style="height:330px">
        <div style="color:#fff;display:flex;flex-direction:column;gap:18px">
          <div class="slab" style="font-weight:800;font-size:112px;line-height:1">¡Sabor que te abraza!</div>
          <div style="font-size:44px;font-weight:600;opacity:.95">Bocaditos de yuca y plátano de Manabí · Recetas y tips cada semana</div>
        </div>
      </div></div>`,
  },

  // ---------- LINKEDIN (página de empresa 1128x191) ----------
  {
    file: 'portada-linkedin.png', w: 1128, h: 191,
    html: `<div style="position:relative;width:1128px;height:191px;background:${C.verde}">
      <img src="escena1.webp" style="position:absolute;right:0;top:0;width:400px;height:191px;object-fit:cover;object-position:40% 45%">
      <div style="position:absolute;right:0;top:0;width:400px;height:191px;background:linear-gradient(90deg,${C.verde} 0%,rgba(82,104,50,0) 55%)"></div>
      <div style="position:absolute;left:270px;top:0;height:191px;display:flex;flex-direction:column;justify-content:center;gap:8px;color:#fff">
        <div class="slab" style="font-weight:800;font-size:29px;line-height:1.05">Bocaditos congelados de yuca y plátano</div>
        <div style="font-size:14px;font-weight:800;letter-spacing:.06em;color:${C.dorado}">RETAIL · FOODSERVICE · DISTRIBUCIÓN · PLANTA CERTIFICADA BPM</div>
      </div></div>`,
  },

  // ---------- X / TWITTER (1500x500) ----------
  {
    file: 'portada-x.png', w: 1500, h: 500,
    html: `<div style="position:relative;width:1500px;height:500px;background:${C.crema};display:flex">
      ${['mini-bolon-de-verde','pan-de-yuca','pipona-de-maduro','boccocitos-verde','mini-muchin-de-yuca'].map(n=>`<img src="${n}.webp" style="width:300px;height:500px;object-fit:cover;object-position:50% 70%">`).join('')}
      <div style="position:absolute;inset:0;background:linear-gradient(0deg,rgba(35,31,32,.75),rgba(35,31,32,0) 60%)"></div>
      <div class="slab" style="position:absolute;right:60px;bottom:40px;color:#fff;font-weight:800;font-size:60px">¡Sabor que te abraza!</div>
    </div>`,
  },
];

// ---------- PORTADAS DE HISTORIAS DESTACADAS (Instagram / Facebook) ----------
const destacadas = [
  ['productos', 'Productos', C.terracota],
  ['recetas', 'Recetas', C.verde],
  ['preparacion', 'Cómo prepararlos', C.dorado],
  ['comprar', 'Dónde comprar', C.terracota],
  ['pedidos', 'Pedidos', C.verde],
  ['negocios', 'Negocios', C.dorado],
  ['nosotros', 'Nosotros', C.terracota],
];
for (const [k, , color] of destacadas) {
  designs.push({
    file: `destacadas/${k}.png`, w: 1080, h: 1920,
    html: `<div style="width:1080px;height:1920px;background:${C.crema};display:grid;place-items:center">
      <div style="width:620px;height:620px;border-radius:50%;background:${color};display:grid;place-items:center">${icon(k, 360, color === C.dorado ? C.carbon : '#fff')}</div></div>`,
  });
}

(async () => {
  fs.mkdirSync(path.join(OUT, 'destacadas'), { recursive: true });
  const browser = await chromium.launch();
  for (const d of designs) {
    const page = await browser.newPage({ viewport: { width: d.w, height: d.h } });
    const tmp = path.join(SRC, '_tmp.html');
    fs.writeFileSync(tmp, `<!doctype html><meta charset="utf-8"><style>${base}</style><body>${d.html}</body>`);
    await page.goto('file://' + tmp);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(OUT, d.file) });
    await page.close();
    console.log('ok', d.file);
  }
  fs.unlinkSync(path.join(SRC, '_tmp.html'));
  await browser.close();
})();
