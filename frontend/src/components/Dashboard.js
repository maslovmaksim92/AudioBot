import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from './ui/dropdown-menu';
import { 
  Home, 
  Users, 
  Building2, 
  Calendar,
  BarChart3,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  MapPin,
  Phone,
  Mail,
  Clock,
  Eye,
  Edit,
  MoreVertical,
  ClipboardCheck,
  Trash2,
  FileText,
  Star,
  Construction,
  Shield
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const [statistics, setStatistics] = useState(null);
  const [houses, setHouses] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Параллельно загружаем все данные
      const [statsResponse, housesResponse, employeesResponse] = await Promise.all([
        axios.get(`${API}/dashboard/statistics`),
        axios.get(`${API}/cleaning/houses?limit=50`),
        axios.get(`${API}/dashboard/employees`)
      ]);

      setStatistics(statsResponse.data.statistics);
      setHouses(housesResponse.data.houses);
      setEmployees(employeesResponse.data.employees);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      console.error('Ошибка загрузки данных:', err);
      setError('Ошибка подключения к Bitrix24. Проверьте настройки интеграции.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-lg font-medium">Загрузка данных из Bitrix24...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Ошибка загрузки</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button onClick={fetchData} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Попробовать снова
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Building2 className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AudioBot Dashboard</h1>
                <p className="text-sm text-gray-500">Система управления домами</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="text-green-600 border-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                Bitrix24 подключен
              </Badge>
              <Button onClick={fetchData} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Обновить
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Всего домов</CardTitle>
                <Home className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.houses.total}</div>
                <p className="text-xs text-muted-foreground">
                  {statistics.houses.total_apartments} квартир, {statistics.houses.with_schedule} с графиками
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Сотрудники</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.employees.total}</div>
                <p className="text-xs text-muted-foreground">
                  {statistics.employees.brigades} бригад
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Управляющие компании</CardTitle>
                <Building2 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.management_companies.total}</div>
                <p className="text-xs text-muted-foreground">
                  Активные партнеры
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Объекты обслуживания</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.houses.total_entrances}</div>
                <p className="text-xs text-muted-foreground">
                  Подъездов в управлении
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="houses" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="houses">Дома</TabsTrigger>
            <TabsTrigger value="brigades">Бригады</TabsTrigger>
            <TabsTrigger value="companies">Управляющие компании</TabsTrigger>
          </TabsList>

          {/* Houses Tab */}
          <TabsContent value="houses" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Building2 className="h-5 w-5 mr-2 text-blue-600" />
                  Многоквартирные дома
                </CardTitle>
                <CardDescription>
                  Объекты недвижимости с правильными данными из CRM
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  {houses.map((house) => (
                    <Card key={house.id} className="border border-gray-200 hover:shadow-md transition-shadow">
                      <CardContent className="p-6">
                        {/* House Header */}
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center">
                            <div className="bg-blue-100 p-2 rounded-lg mr-4">
                              <Building2 className="h-6 w-6 text-blue-600" />
                            </div>
                            <div>
                              <h3 className="text-xl font-semibold text-gray-900 mb-1">
                                {house.address}
                              </h3>
                              <div className="flex items-center text-sm text-gray-500">
                                <MapPin className="h-4 w-4 mr-1" />
                                ID: {house.id}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Правильные данные - статистика дома */}
                        <div className="bg-gray-50 rounded-lg p-4 mb-4">
                          <h4 className="text-sm font-medium text-gray-700 mb-3">Правильные данные</h4>
                          <div className="grid grid-cols-3 gap-6">
                            <div className="text-center">
                              <div className="text-3xl font-bold text-green-600 mb-1">{house.apartments}</div>
                              <div className="text-sm text-gray-600">Квартир</div>
                            </div>
                            <div className="text-center">
                              <div className="text-3xl font-bold text-blue-600 mb-1">{house.entrances}</div>
                              <div className="text-sm text-gray-600">Подъездов</div>
                            </div>
                            <div className="text-center">
                              <div className="text-3xl font-bold text-orange-600 mb-1">{house.floors}</div>
                              <div className="text-sm text-gray-600">Этажей</div>
                            </div>
                          </div>
                        </div>

                        {/* Управляющая компания */}
                        <div className="mb-4">
                          <div className="flex items-center mb-2">
                            <Shield className="h-4 w-4 text-blue-600 mr-2" />
                            <span className="text-sm font-medium text-gray-700">Управляющая компания:</span>
                          </div>
                          <div className="pl-6">
                            <Badge variant="secondary" className="font-medium text-base px-3 py-1">
                              {house.management_company}
                            </Badge>
                          </div>
                        </div>

                        {/* График уборки */}
                        {house.september_schedule && house.september_schedule !== 'Не указан' && (
                          <div className="mb-4">
                            <div className="flex items-center mb-2">
                              <Calendar className="h-4 w-4 text-green-600 mr-2" />
                              <span className="text-sm font-medium text-gray-700">График уборки:</span>
                            </div>
                            <div className="pl-6 bg-green-50 border-l-4 border-green-400 p-3 rounded-r-lg">
                              <div className="text-sm text-green-800 font-medium">
                                {house.september_schedule}
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Действия */}
                        <div className="flex gap-3 pt-4 border-t border-gray-200">
                          <Button variant="outline" size="sm" className="flex-1">
                            <Calendar className="h-4 w-4 mr-2" />
                            График
                          </Button>
                          <Button variant="outline" size="sm" className="flex-1">
                            <Eye className="h-4 w-4 mr-2" />
                            Детали
                          </Button>
                          <Button variant="outline" size="sm" className="flex-1">
                            <ClipboardCheck className="h-4 w-4 mr-2" />
                            Задачи
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Summary Card */}
                <Card className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900 mb-2">Сводка по домам</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">Всего домов:</span>
                            <span className="font-bold text-blue-600 ml-2">{houses.length}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Всего квартир:</span>
                            <span className="font-bold text-green-600 ml-2">
                              {houses.reduce((sum, house) => sum + house.apartments, 0)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Всего подъездов:</span>
                            <span className="font-bold text-purple-600 ml-2">
                              {houses.reduce((sum, house) => sum + house.entrances, 0)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Средняя этажность:</span>
                            <span className="font-bold text-orange-600 ml-2">
                              {Math.round(houses.reduce((sum, house) => sum + house.floors, 0) / houses.length)}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="hidden md:block">
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                          <BarChart3 className="h-8 w-8 text-blue-600" />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Brigades Tab */}
          <TabsContent value="brigades" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Рабочие бригады</CardTitle>
                <CardDescription>
                  Организационная структура и сотрудники
                </CardDescription>
              </CardHeader>
              <CardContent>
                {statistics && (
                  <div className="grid gap-6">
                    {statistics.employees.by_brigade.map((brigade) => (
                      <Card key={brigade.id} className="p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold">{brigade.name}</h3>
                          <Badge variant="outline">
                            {brigade.employees.length} сотрудников
                          </Badge>
                        </div>
                        <div className="grid gap-3">
                          {brigade.employees.map((employee) => (
                            <div key={employee.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div>
                                <p className="font-medium">{employee.name}</p>
                                <p className="text-sm text-gray-600">{employee.position}</p>
                              </div>
                              <div className="text-right text-sm text-gray-500">
                                {employee.email && (
                                  <div className="flex items-center">
                                    <Mail className="h-3 w-3 mr-1" />
                                    {employee.email}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Companies Tab */}
          <TabsContent value="companies" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Управляющие компании</CardTitle>
                <CardDescription>
                  Партнеры и контрагенты
                </CardDescription>
              </CardHeader>
              <CardContent>
                {statistics && (
                  <div className="grid gap-4">
                    {statistics.management_companies.list.map((company, index) => (
                      <Card key={index} className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Building2 className="h-5 w-5 text-blue-600 mr-3" />
                            <div>
                              <h3 className="font-semibold">{company}</h3>
                              <p className="text-sm text-gray-600">Управляющая компания</p>
                            </div>
                          </div>
                          <Badge variant="secondary">Активная</Badge>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Footer */}
        {lastUpdated && (
          <div className="mt-8 text-center text-sm text-gray-500">
            Последнее обновление: {lastUpdated}
          </div>
        )}
      </main>
    </div>
  );
}