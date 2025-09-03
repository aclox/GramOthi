import { Router } from 'express';
import quizzes from './quizzes.js';
import polls from './polls.js';
import chat from './messages.js';
import { getDb } from '../lib/db.js';

export default function registerRoutes(app) {
  const api = Router();
  api.use('/quizzes', quizzes);
  api.use('/polls', polls);
  api.use('/messages', chat);

  // Minimal classes routes for setup/testing
  api.post('/classes', async (req, res) => {
    const { title = 'Untitled' } = req.body || {};
    const { v4: uuid } = await import('uuid');
    const id = uuid();
    await getDb().query('insert into classes(id, title) values($1,$2)', [id, title]);
    res.json({ id, title });
  });

  api.get('/classes/:id', async (req, res) => {
    const { rows } = await getDb().query('select * from classes where id=$1', [req.params.id]);
    if (!rows[0]) return res.status(404).json({ error: 'not found' });
    res.json(rows[0]);
  });
  app.use('/api', api);
}


