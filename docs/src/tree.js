export const TREE = {
  start: [
    {
      id: 'destino',
      title: '¿Para quién es este libro?',
      options: [
        { label: 'Para mí', value: 'propio' },
        { label: 'Es un regalo', value: 'regalo' },
      ],
    },
    {
      id: 'modo',
      title: '¿Cómo prefieres que te ayudemos a elegir?',
      options: [
        { label: 'Ya tengo una idea en mente', value: 'idea' },
        { label: 'Quiero descubrir opciones nuevas', value: 'discover' },
      ],
    },
  ],

  idea: [
    { id: 'tipo', title: '¿Ficción o no ficción?', options: ['Ficción','No ficción','Me da igual'] },
    { id: 'ficGenero', title: 'Elige el género', when: d => d.tipo === 'Ficción', options: ['Romance','Rom-com','Thriller','Suspenso','Policial','Aventura','Misterio','Humor','Fantasía ligera','Realismo contemporáneo','Literaria'] },
    { id: 'ficLongitud', title: 'Extensión', when: d => d.tipo === 'Ficción', options: ['Corto','Medio','Largo'] },

    { id: 'nfTema', title: 'Tema principal', when: d => d.tipo === 'No ficción', options: ['Historia','Ciencia','Psicología','Negocios','Divulgación científica','Biografías'] },
    { id: 'nfTono', title: 'Tono preferido', when: d => d.tipo === 'No ficción', options: ['Reflexivo','Inspirador','Agridulce','Esperanzador'] },
    { id: 'nfLongitud', title: 'Extensión', when: d => d.tipo === 'No ficción', options: ['Corto','Medio','Largo'] },

    { id: 'formato', title: 'Formato', options: ['Tapa blanda','Tapa dura','Cualquiera'] },
    { id: 'precio', title: 'Presupuesto máximo', type: 'range' },
    { id: 'publico', title: '¿Para quién es?', options: ['Infantil','Juvenil','Adulto'] },
    { id: 'evitar', title: '¿Quieres evitar algo?', multi: true, options: ['violencia','sexo','lenguaje','duelo'] },
  ],

  discover: [
    { id: 'animo', title: '¿Qué ánimo buscas?', options: ['Desconectar','Emoción','Romántico','Reflexivo','Aprender','Inspirarme','Sorpréndeme'] },
    { id: 'temas', title: 'Temas que te interesan (máx. 2)', multi: true, max: 2, options: ['Romance','Suspenso','Aventura','Humor','Historia','Ciencia','Psicología','Biografías'] },
    { id: 'extension', title: 'Extensión', options: ['Corto','Medio','Largo'] },
    { id: 'formato', title: 'Formato', options: ['Tapa blanda','Tapa dura','Cualquiera'] },
    { id: 'precio', title: 'Presupuesto máximo', type: 'range' },
    { id: 'publico', title: '¿Para quién es?', options: ['Infantil','Juvenil','Adulto'] },
    { id: 'evitar', title: '¿Quieres evitar algo?', multi: true, options: ['violencia','sexo','lenguaje','duelo'] },
  ],
};
