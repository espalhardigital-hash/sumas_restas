
import React, { useState, useEffect } from 'react';
import { User, UserRole } from '../types';
import { getAllUsers, saveUser, deleteUser, getStorageUsage, getAllScores, getUserDetailedAnalytics, adminCreateUser, adminChangePassword, getAvatarUrl, deleteScoreById } from '../services/storageService';
import {
  ArrowLeft, Users, Shield, Activity, Database, Search,
  Edit, Trash2, UserX, UserCheck, Plus, X, Key, Check, Calendar, Clock, BarChart2
} from 'lucide-react';

interface Props {
  onBack: () => void;
}

// Helper to format dates as "Jueves, 5 Abril 2026" (No "de", capitalized)
const formatFriendlyDate = (dateStr: string, includeTime: boolean = true) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const options: Intl.DateTimeFormatOptions = {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    ...(includeTime && { hour: '2-digit', minute: '2-digit' })
  };
  
  const formatted = includeTime 
    ? d.toLocaleString('es-ES', options) 
    : d.toLocaleDateString('es-ES', options);

  return formatted
    .replace(/ de /g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const AdminPanel: React.FC<Props> = ({ onBack }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [filter, setFilter] = useState('');

  // Modals State
  const [showUserModal, setShowUserModal] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [showAllScoresModal, setShowAllScoresModal] = useState(false);

  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordUserId, setPasswordUserId] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [statsUser, setStatsUser] = useState<User | null>(null);
  const [userStatsData, setUserStatsData] = useState<any>(null);
  const [allScores, setAllScores] = useState<any[]>([]);
  const [statsTab, setStatsTab] = useState<'category' | 'difficulty'>('category');
  const [sortConfig, setSortConfig] = useState<{key: 'date' | 'score', direction: 'asc' | 'desc'}>({key: 'date', direction: 'desc'});

  // Global Stats
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    totalGamesPlayed: 0,
    storage: '0 KB'
  });

  // User Form State
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'USER' as UserRole,
    status: 'ACTIVE' as 'ACTIVE' | 'BANNED'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const allUsers = await getAllUsers();
    const scores = await getAllScores();

    setUsers(allUsers);
    setAllScores(scores);

    // Calculate Global Stats
    setStats({
      totalUsers: allUsers.length,
      activeUsers: allUsers.filter(u => u.status === 'ACTIVE').length,
      totalGamesPlayed: scores.length,
      storage: getStorageUsage()
    });
  };

  const handleCreate = () => {
    setEditingUser(null);
    setFormData({ username: '', email: '', password: '', role: 'USER', status: 'ACTIVE' });
    setShowUserModal(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      password: user.password,
      role: user.role,
      status: user.status
    });
    setShowUserModal(true);
  };

  const handleViewStats = async (user: User) => {
    setStatsUser(user);
    // Reset data before fetching
    setUserStatsData(null);
    setShowStatsModal(true);
    
    const data = await getUserDetailedAnalytics(user.username);
    // If data is null, we'll handle it in the modal UI
    setUserStatsData(data || { history: [], totalGames: 0 });
  };

  const handleDelete = async (id: string) => {
    if (confirm('¿Estás seguro de eliminar este usuario permanentemente?')) {
      await deleteUser(id);
      loadData();
    }
  };

  const handleSaveUser = async (e: React.FormEvent) => {
    e.preventDefault();

    if (editingUser) {
      // Editing existing user
      const newUser: User = {
        ...editingUser,
        ...formData,
        password: formData.password || editingUser.password
      };
      await saveUser(newUser);
    } else {
      // Creating new user
      const result = await adminCreateUser({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        role: formData.role
      });
      if (!result.success) {
        alert(result.message || 'Error al crear usuario');
        return;
      }
    }

    setShowUserModal(false);
    loadData();
  };

  const handleChangePassword = (user: User) => {
    setPasswordUserId(user.id);
    setNewPassword('');
    setShowPasswordModal(true);
  };

  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordUserId || !newPassword) return;

    const result = await adminChangePassword(passwordUserId, newPassword);
    if (result.success) {
      alert('Contraseña actualizada correctamente');
      setShowPasswordModal(false);
    } else {
      alert(result.message || 'Error al cambiar contraseña');
    }
  };

  const toggleStatus = async (user: User) => {
    const newStatus = user.status === 'ACTIVE' ? 'BANNED' : 'ACTIVE';
    await saveUser({ ...user, status: newStatus });
    loadData();
  };

  const sortedHistory = React.useMemo(() => {
    if (!userStatsData?.history) return [];
    return [...userStatsData.history].sort((a, b) => {
      if (sortConfig.key === 'date') {
        const dateA = a.rawDate ? new Date(a.rawDate).getTime() : 0;
        const dateB = b.rawDate ? new Date(b.rawDate).getTime() : 0;
        return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
      } else {
        return sortConfig.direction === 'asc' ? a.score - b.score : b.score - a.score;
      }
    });
  }, [userStatsData?.history, sortConfig]);

  const toggleSort = (key: 'date' | 'score') => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const filteredUsers = users.filter(u =>
    u.username.toLowerCase().includes(filter.toLowerCase()) ||
    u.email.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="w-full max-w-6xl h-[90vh] flex flex-col animate-fade-in relative">

      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-white/10 rounded-full transition-colors bg-white/5 border border-white/10"
          >
            <ArrowLeft className="text-white" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Shield className="text-red-500" /> Panel de Administración
            </h1>
            <p className="text-gray-400 text-sm">Gestión avanzada del sistema</p>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-black/30 border border-white/10 p-4 rounded-xl flex items-center justify-between">
          <div><p className="text-gray-400 text-xs uppercase">Usuarios</p><p className="text-2xl font-bold text-white">{stats.totalUsers}</p></div>
          <Users className="text-blue-400 opacity-50" />
        </div>
        <div 
          onClick={() => setShowAllScoresModal(true)}
          className="bg-black/30 border border-white/10 p-4 rounded-xl flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors group"
        >
          <div><p className="text-gray-400 text-xs uppercase">Partidas</p><p className="text-2xl font-bold text-green-400">{stats.totalGamesPlayed}</p></div>
          <Activity className="text-green-400 group-hover:scale-110 transition-transform" />
        </div>
        <div className="bg-black/30 border border-white/10 p-4 rounded-xl flex items-center justify-between">
          <div><p className="text-gray-400 text-xs uppercase">Activos</p><p className="text-2xl font-bold text-yellow-400">{stats.activeUsers}</p></div>
          <UserCheck className="text-yellow-400 opacity-50" />
        </div>
        <div className="bg-black/30 border border-white/10 p-4 rounded-xl flex items-center justify-between">
          <div><p className="text-gray-400 text-xs uppercase">Storage DB</p><p className="text-2xl font-bold text-purple-400">{stats.storage}</p></div>
          <Database className="text-purple-400 opacity-50" />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl flex flex-col">

        {/* Toolbar */}
        <div className="p-4 border-b border-white/10 flex flex-col md:flex-row justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
            <input
              type="text"
              placeholder="Buscar por nombre o email..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full bg-black/20 border border-white/10 rounded-lg py-2 pl-10 pr-4 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg flex items-center gap-2 text-white font-bold"
          >
            <Plus size={18} /> Nuevo Usuario
          </button>
        </div>

        {/* User Table */}
        <div className="flex-1 overflow-auto custom-scrollbar">
          <table className="w-full text-left border-collapse">
            <thead className="bg-black/20 text-gray-400 text-xs uppercase sticky top-0 backdrop-blur-md">
              <tr>
                <th className="p-4">Usuario</th>
                <th className="p-4 hidden sm:table-cell">Detalles</th>
                <th className="p-4">Estado</th>
                <th className="p-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredUsers.map(user => (
                <tr key={user.id} className="hover:bg-white/5 transition-colors">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full overflow-hidden border border-white/20 flex items-center justify-center bg-gray-700">
                        {user.avatar ? <img src={getAvatarUrl(user.avatar)} className="w-full h-full object-cover" /> : <span className="font-bold text-gray-400">{user.username[0]}</span>}
                      </div>
                      <div>
                        <div className="font-bold text-white">{user.username}</div>
                        <div className="text-xs text-gray-500 hidden sm:block">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 hidden sm:table-cell">
                    <div className="flex flex-col">
                      <span className={`text-xs font-bold ${user.role === 'ADMIN' ? 'text-red-400' : 'text-blue-400'}`}>{user.role}</span>
                      <span className="text-xs text-gray-500">Reg: {formatFriendlyDate(user.createdAt, false) || 'Desconocido'}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${user.status === 'ACTIVE' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                      {user.status === 'ACTIVE' ? 'Activo' : 'Baneado'}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center justify-center gap-2">
                      <button onClick={() => handleViewStats(user)} className="p-2 rounded-lg bg-purple-500/20 hover:bg-purple-500/40 text-purple-300" title="Ver Estadísticas">
                        <BarChart2 size={16} />
                      </button>
                      <button onClick={() => toggleStatus(user)} className="p-2 rounded-lg bg-white/5 hover:bg-white/20 text-gray-300" title={user.status === 'ACTIVE' ? 'Desactivar' : 'Activar'}>
                        {user.status === 'ACTIVE' ? <UserX size={16} /> : <UserCheck size={16} className="text-green-400" />}
                      </button>
                      <button onClick={() => handleEdit(user)} className="p-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/40 text-blue-300" title="Editar">
                        <Edit size={16} />
                      </button>
                      <button onClick={() => handleChangePassword(user)} className="p-2 rounded-lg bg-yellow-500/20 hover:bg-yellow-500/40 text-yellow-300" title="Cambiar Contraseña">
                        <Key size={16} />
                      </button>
                      <button onClick={() => handleDelete(user.id)} className="p-2 rounded-lg bg-red-500/20 hover:bg-red-500/40 text-red-300" title="Eliminar">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredUsers.length === 0 && (
            <div className="p-8 text-center text-gray-500">No se encontraron usuarios.</div>
          )}
        </div>
      </div>

      {/* MODAL 1: Create/Edit User */}
      {showUserModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in p-4">
          <div className="bg-[#1e293b] border border-white/10 p-6 rounded-2xl w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white">{editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}</h3>
              <button onClick={() => setShowUserModal(false)} className="text-gray-400 hover:text-white"><X size={24} /></button>
            </div>

            <form onSubmit={handleSaveUser} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 uppercase font-bold">Nombre</label>
                <input required value={formData.username} onChange={e => setFormData({ ...formData, username: e.target.value })} className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:border-blue-500 outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-400 uppercase font-bold">Email</label>
                <input required type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:border-blue-500 outline-none" disabled={!!editingUser} />
              </div>
              {!editingUser && (
                <div>
                  <label className="text-xs text-gray-400 uppercase font-bold">Contraseña</label>
                  <input required type="password" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:border-blue-500 outline-none" placeholder="Contraseña inicial" />
                </div>
              )}
              {/* Password field removed: Use separate password change function */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-400 uppercase font-bold">Rol</label>
                  <select value={formData.role} onChange={e => setFormData({ ...formData, role: e.target.value as UserRole })} className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:border-blue-500 outline-none">
                    <option value="USER">Usuario</option>
                    <option value="ADMIN">Administrador</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 uppercase font-bold">Estado</label>
                  <select value={formData.status} onChange={e => setFormData({ ...formData, status: e.target.value as any })} className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:border-blue-500 outline-none">
                    <option value="ACTIVE">Activo</option>
                    <option value="BANNED">Baneado</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setShowUserModal(false)} className="px-4 py-2 rounded-lg text-gray-400 hover:text-white">Cancelar</button>
                <button type="submit" className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold flex items-center gap-2">
                  <Check size={18} /> Guardar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: User Statistics (ENHANCED) */}
      {showStatsModal && statsUser && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in p-4">
          <div className="bg-[#1e293b] border border-white/10 p-0 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Header */}
            <div className="bg-white/5 p-6 flex items-center gap-4 border-b border-white/10">
              <div className="w-16 h-16 rounded-full overflow-hidden border border-white/20 flex items-center justify-center bg-gray-700 mr-4">
                {statsUser.avatar ? <img src={getAvatarUrl(statsUser.avatar)} className="w-full h-full object-cover" /> : <span className="text-2xl font-bold text-gray-400">{statsUser.username[0]}</span>}
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-white">{statsUser.username}</h3>
                <p className="text-gray-400 text-sm">{statsUser.email}</p>
                <div className="flex gap-4 mt-1 text-xs">
                  <span className="text-blue-400">Nivel Desbloqueado: {(statsUser.unlockedLevel ?? 0) + 1}</span>
                </div>
              </div>
              <button onClick={() => setShowStatsModal(false)} className="text-gray-400 hover:text-white self-start"><X size={24} /></button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
              {!userStatsData ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                  <Activity className="animate-spin mb-4" size={32} />
                  <p>Cargando estadísticas...</p>
                </div>
              ) : (
                <>
                  <h4 className="text-sm font-bold text-gray-400 uppercase mb-4 flex items-center gap-2">
                    <Activity size={16} /> Historial de Partidas
                  </h4>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead className="text-xs text-gray-400 uppercase bg-white/5">
                        <tr>
                          <th className="p-3 cursor-pointer hover:text-white transition-colors" onClick={() => toggleSort('date')}>
                            Fecha {sortConfig.key === 'date' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                          </th>
                          <th className="p-3">Categoría</th>
                          <th className="p-3 text-center">Nivel</th>
                          <th className="p-3 text-center cursor-pointer hover:text-white transition-colors" onClick={() => toggleSort('score')}>
                            Puntaje {sortConfig.key === 'score' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                          </th>
                          <th className="p-3 text-center">Errores</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {sortedHistory.map((record: any) => (
                          <tr key={record.id} className="hover:bg-white/5">
                            <td className="p-3 text-gray-300 whitespace-nowrap">
                              {formatFriendlyDate(record.rawDate || record.date)}
                            </td>
                            <td className="p-3 font-medium text-white capitalize">
                              {record.category === 'mixed_add_sub' ? 'Suma/Resta' :
                                record.category === 'mixed_mult_add' ? 'Mult/Op' :
                                  record.category === 'all_mixed' ? 'Experto' :
                                    record.category}
                            </td>
                            <td className="p-3 text-center text-blue-300">
                              {record.difficulty === 'easy' ? 'Nivel 1' :
                                record.difficulty === 'easy_medium' ? 'Nivel 2' :
                                  record.difficulty === 'medium' ? 'Nivel 3' :
                                    record.difficulty === 'medium_hard' ? 'Nivel 4' :
                                      record.difficulty === 'hard' ? 'Nivel 5' :
                                        record.difficulty}
                            </td>
                            <td className="p-3 text-center">
                              <span className={`${record.score >= 80 ? 'text-green-400' : record.score >= 60 ? 'text-yellow-400' : 'text-red-400'} font-bold`}>
                                {record.score}%
                              </span>
                            </td>
                            <td className="p-3 text-center text-red-400 font-bold">
                              {record.errorCount}
                            </td>
                          </tr>
                        ))}
                        {sortedHistory.length === 0 && (
                          <tr><td colSpan={5} className="p-4 text-center text-gray-500">Sin historial de partidas.</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: All Scores (General Scores) */}
      {showAllScoresModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in p-4">
          <div className="bg-[#1e293b] border border-white/10 p-0 rounded-2xl w-full max-w-5xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="bg-white/5 p-6 flex justify-between items-center border-b border-white/10">
              <div>
                <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Activity className="text-green-400" /> Puntuaciones Generales
                </h3>
                <p className="text-gray-400 text-sm">Todas las partidas registradas en el sistema</p>
              </div>
              <button onClick={() => setShowAllScoresModal(false)} className="text-gray-400 hover:text-white"><X size={24} /></button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead className="text-xs text-gray-400 uppercase bg-white/5 sticky top-0 backdrop-blur-md">
                    <tr>
                      <th className="p-3">Fecha</th>
                      <th className="p-3">Usuario</th>
                      <th className="p-3">Categoría</th>
                      <th className="p-3 text-center">Puntaje</th>
                      <th className="p-3 text-center">Errores</th>
                      <th className="p-3 text-center">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {[...allScores].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).map((record: any) => (
                      <tr key={record.id} className="hover:bg-white/5">
                        <td className="p-3 text-gray-300 whitespace-nowrap">
                          {formatFriendlyDate(record.date)}
                        </td>
                        <td className="p-3 font-bold text-blue-400">
                          {record.user}
                        </td>
                        <td className="p-3 text-white capitalize">
                          {record.category?.replace(/_/g, ' ') || 'General'}
                        </td>
                        <td className="p-3 text-center">
                          <span className={`${record.score >= 80 ? 'text-green-400' : record.score >= 60 ? 'text-yellow-400' : 'text-red-400'} font-bold`}>
                            {record.score}%
                          </span>
                        </td>
                        <td className="p-3 text-center text-red-400 font-bold">
                          {record.errorCount}
                        </td>
                        <td className="p-3 text-center">
                          <button 
                            onClick={async () => {
                              if (confirm('¿Eliminar esta puntuación?')) {
                                await deleteScoreById(record.id);
                                loadData();
                              }
                            }}
                            className="p-1 hover:bg-red-500/20 text-red-400 rounded transition-colors"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {allScores.length === 0 && (
                      <tr><td colSpan={6} className="p-8 text-center text-gray-500">No hay partidas registradas.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: Change Password */}
      {showPasswordModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in p-4">
          <div className="bg-[#1e293b] border border-white/10 p-6 rounded-2xl w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Key className="text-yellow-400" /> Cambiar Contraseña
              </h3>
              <button onClick={() => setShowPasswordModal(false)} className="text-gray-400 hover:text-white"><X size={24} /></button>
            </div>

            <form onSubmit={handleSavePassword} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 uppercase font-bold">Nueva Contraseña</label>
                <input
                  required
                  type="password"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:border-yellow-500 outline-none"
                  placeholder="Ingrese la nueva contraseña"
                  minLength={6}
                />
              </div>
              <p className="text-xs text-gray-500">Mínimo 6 caracteres.</p>

              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setShowPasswordModal(false)} className="px-4 py-2 rounded-lg text-gray-400 hover:text-white">Cancelar</button>
                <button type="submit" className="px-6 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg font-bold flex items-center gap-2">
                  <Key size={18} /> Actualizar Contraseña
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminPanel;
