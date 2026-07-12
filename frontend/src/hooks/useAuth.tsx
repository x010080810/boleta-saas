import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { authApi } from '../services/api';
import type { User, Company } from '../types';

interface AuthContextType {
  user: User | null;
  companies: Company[];
  selectedCompany: Company | null;
  loading: boolean;
  login: (email: string, password: string, isSuper?: boolean) => Promise<void>;
  logout: () => void;
  selectCompany: (company: Company) => void;
  isSuperAdmin: boolean;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      authApi.me()
        .then((res) => {
          setUser(res.data);
          const saved = localStorage.getItem('selected_company');
          if (saved) {
            setSelectedCompany(JSON.parse(saved));
          }
        })
        .catch(() => {
          localStorage.clear();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string, isSuper = false) => {
    const apiCall = isSuper ? authApi.superLogin : authApi.login;
    const res = await apiCall(email, password);
    localStorage.setItem('access_token', res.data.access_token);
    localStorage.setItem('refresh_token', res.data.refresh_token);
    setUser(res.data.user);

    if (res.data.companies?.length > 0) {
      setCompanies(res.data.companies);
      setSelectedCompany(res.data.companies[0]);
      localStorage.setItem('selected_company', JSON.stringify(res.data.companies[0]));
    }
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
    setCompanies([]);
    setSelectedCompany(null);
  };

  const selectCompany = (company: Company) => {
    setSelectedCompany(company);
    localStorage.setItem('selected_company', JSON.stringify(company));
  };

  return (
    <AuthContext.Provider value={{
      user, companies, selectedCompany, loading,
      login, logout, selectCompany,
      isSuperAdmin: user?.type === 'super_admin',
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
