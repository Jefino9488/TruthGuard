"use client"; // Required for useState and useEffect

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Shield, TrendingUp, AlertTriangle, CheckCircle, RefreshCw, Database, Brain, Newspaper } from "lucide-react"; // Added Database, Brain, Newspaper
import { BiasChart } from "@/components/bias-chart";
import { SourceComparison } from "@/components/source-comparison";
import { ThreatLevel } from "@/components/threat-level";
import { RecentArticles } from "@/components/recent-articles"; // This might be replaced or augmented by the live feed
import { BiasHeatmap } from "@/components/bias-heatmap";

// 1. Define Types/Interfaces
interface DashboardStatistics {
  total_articles_processed: number;
  total_bias_detected: number;
  total_misinformation_risk: number;
  overall_accuracy_rate: string;
}

interface LiveFeedArticle {
  _id: string;
  title: string;
  source?: string; // Matching Flask's 'source' field for articles
  published_at: string;
}

interface SystemStatus {
  mongodb: 'connected' | 'disconnected' | 'unknown';
  google_api: 'configured' | 'not_configured' | 'unknown';
  news_api: 'configured' | 'not_configured' | 'unknown';
}

export default function DashboardPage() {
  // 2. Add State Variables
  const [dashboardStats, setDashboardStats] = useState<DashboardStatistics | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  const [liveFeedArticles, setLiveFeedArticles] = useState<LiveFeedArticle[]>([]);
  const [isLoadingLiveFeed, setIsLoadingLiveFeed] = useState(true);
  const [liveFeedError, setLiveFeedError] = useState<string | null>(null);

  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isLoadingSystemStatus, setIsLoadingSystemStatus] = useState(true);
  const [systemStatusError, setSystemStatusError] = useState<string | null>(null);

  const API_BASE_URL = "http://localhost:5000"; // Make sure this matches your Flask backend URL

  // 3. Implement useEffect for Data Fetching
  useEffect(() => {
    // Fetch Dashboard Statistics
    const fetchStats = async () => {
      setIsLoadingStats(true);
      setStatsError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/statistics`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: DashboardStatistics = await response.json();
        setDashboardStats(data);
      } catch (error: any) {
        setStatsError(error.message || "Failed to fetch statistics");
        console.error("Error fetching dashboard stats:", error);
      } finally {
        setIsLoadingStats(false);
      }
    };

    // Fetch Live Feed Articles
    const fetchLiveFeed = async () => {
      setIsLoadingLiveFeed(true);
      setLiveFeedError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/articles?sort_by=published_at&sort_order=desc&limit=5`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setLiveFeedArticles(data.articles || []); // Ensure to access data.articles
      } catch (error: any) {
        setLiveFeedError(error.message || "Failed to fetch live feed");
        console.error("Error fetching live feed:", error);
      } finally {
        setIsLoadingLiveFeed(false);
      }
    };

    // Fetch System Status
    const fetchSystemStatus = async () => {
      setIsLoadingSystemStatus(true);
      setSystemStatusError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/system/status`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: SystemStatus = await response.json();
        setSystemStatus(data);
      } catch (error: any) {
        setSystemStatusError(error.message || "Failed to fetch system status");
        console.error("Error fetching system status:", error);
      } finally {
        setIsLoadingSystemStatus(false);
      }
    };

    fetchStats();
    fetchLiveFeed();
    fetchSystemStatus();
  }, []); // Empty dependency array means this runs once on mount

  const handleRefresh = () => {
    // Re-fetch all data
    setIsLoadingStats(true);
    setIsLoadingLiveFeed(true);
    setIsLoadingSystemStatus(true);
    // Simulate re-fetching by calling useEffect's internal functions again
    // In a real app, you might abstract fetch functions to call them here
    const fetchStats = async () => {
      setIsLoadingStats(true); setStatsError(null); try { const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/statistics`); if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`); const data: DashboardStatistics = await response.json(); setDashboardStats(data); } catch (error: any) { setStatsError(error.message || "Failed to fetch statistics"); } finally { setIsLoadingStats(false); }
    };
    const fetchLiveFeed = async () => {
      setIsLoadingLiveFeed(true); setLiveFeedError(null); try { const response = await fetch(`${API_BASE_URL}/articles?sort_by=published_at&sort_order=desc&limit=5`); if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`); const data = await response.json(); setLiveFeedArticles(data.articles || []); } catch (error: any) { setLiveFeedError(error.message || "Failed to fetch live feed"); } finally { setIsLoadingLiveFeed(false); }
    };
    const fetchSystemStatus = async () => {
      setIsLoadingSystemStatus(true); setSystemStatusError(null); try { const response = await fetch(`${API_BASE_URL}/api/v1/system/status`); if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`); const data: SystemStatus = await response.json(); setSystemStatus(data); } catch (error: any) { setSystemStatusError(error.message || "Failed to fetch system status"); } finally { setIsLoadingSystemStatus(false); }
    };
    fetchStats();
    fetchLiveFeed();
    fetchSystemStatus();
  };


  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Shield className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold">TruthGuard Dashboard</h1>
                <p className="text-sm text-gray-600">Real-time bias and misinformation detection</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className={
                isLoadingSystemStatus ? "text-gray-600 border-gray-600" :
                systemStatusError ? "text-red-600 border-red-600" :
                (systemStatus?.mongodb === 'connected' && systemStatus?.google_api === 'configured' && systemStatus?.news_api === 'configured')
                ? "text-green-600 border-green-600" : "text-red-600 border-red-600"
              }>
                <CheckCircle className="h-3 w-3 mr-1" />
                {isLoadingSystemStatus ? 'System Status: Loading...' : systemStatusError ? 'System Status: Error' :
                  (systemStatus?.mongodb === 'connected' && systemStatus?.google_api === 'configured' && systemStatus?.news_api === 'configured')
                  ? 'System Online' : 'System Issues'}
              </Badge>
              <Button size="sm" variant="outline" onClick={handleRefresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Key Metrics - Updated with dynamic data */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Articles Processed</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoadingStats ? '...' : statsError ? 'Error' : dashboardStats?.total_articles_processed ?? 'N/A'}</div>
              {/* <p className="text-xs text-muted-foreground">+12% from yesterday</p>  Dynamic percentage change can be added later */}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Bias Detected</CardTitle>
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoadingStats ? '...' : statsError ? 'Error' : dashboardStats?.total_bias_detected ?? 'N/A'}</div>
              {/* <p className="text-xs text-muted-foreground">-8% from yesterday</p> */}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Misinformation Risk</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoadingStats ? '...' : statsError ? 'Error' : dashboardStats?.total_misinformation_risk ?? 'N/A'}</div>
              {/* <p className="text-xs text-muted-foreground">+3% from yesterday</p> */}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Accuracy Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isLoadingStats ? '...' : statsError ? 'Error' : dashboardStats?.overall_accuracy_rate ?? 'N/A'}</div>
              {/* <p className="text-xs text-muted-foreground">+0.2% from yesterday</p> */}
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="bias-analysis">Bias Analysis</TabsTrigger>
            <TabsTrigger value="sources">Sources</TabsTrigger>
            <TabsTrigger value="real-time">Real-time</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Bias Distribution</CardTitle>
                  <CardDescription>Current bias patterns across all sources</CardDescription>
                </CardHeader>
                <CardContent>
                  <BiasChart />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Threat Assessment</CardTitle>
                  <CardDescription>Real-time misinformation risk levels</CardDescription>
                </CardHeader>
                <CardContent>
                  <ThreatLevel />
                </CardContent>
              </Card>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Recent Analysis</CardTitle>
                <CardDescription>Latest articles processed by the AI system</CardDescription>
              </CardHeader>
              <CardContent>
                {/* This component might be replaced or augmented by the live feed logic below.
                    For now, keeping it for other potential uses. */}
                <RecentArticles />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="bias-analysis" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Bias Heatmap</CardTitle>
                <CardDescription>Visual representation of bias patterns across topics and sources</CardDescription>
              </CardHeader>
              <CardContent>
                <BiasHeatmap />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sources" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Source Comparison</CardTitle>
                <CardDescription>Bias analysis across different news sources</CardDescription>
              </CardHeader>
              <CardContent>
                <SourceComparison />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="real-time" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Live Feed (Last 5 Analyzed)</CardTitle>
                  <CardDescription>Real-time article processing updates</CardDescription>
                </CardHeader>
                <CardContent>
                  {isLoadingLiveFeed && <p>Loading live feed...</p>}
                  {liveFeedError && <p className="text-red-500">Error: {liveFeedError}</p>}
                  {!isLoadingLiveFeed && !liveFeedError && liveFeedArticles.length === 0 && <p>No articles in the feed.</p>}
                  <div className="space-y-4">
                    {liveFeedArticles.map((article) => (
                      <div key={article._id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                           <CheckCircle className="w-4 h-4 text-green-500" /> {/* Assuming 'analyzed' status */}
                          <div>
                            <p className="font-medium truncate w-60" title={article.title}>{article.title}</p>
                            <p className="text-sm text-gray-600">
                              Source: {article.source || 'N/A'} - Published: {new Date(article.published_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <Badge variant="outline" className="text-green-600 border-green-500">Analyzed</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>System Component Status</CardTitle>
                  <CardDescription>Backend services and API health</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {isLoadingSystemStatus && <p>Loading system status...</p>}
                    {systemStatusError && <p className="text-red-500">Error: {systemStatusError}</p>}
                    {!isLoadingSystemStatus && !systemStatusError && !systemStatus && <p>No system status available.</p>}

                    {systemStatus && (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="flex items-center"><Database className="w-4 h-4 mr-2 text-blue-500" />MongoDB</span>
                          <Badge className={systemStatus.mongodb === 'connected' ? 'bg-green-100 text-green-800' : systemStatus.mongodb === 'disconnected' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}>
                            {systemStatus.mongodb || 'Unknown'}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="flex items-center"><Brain className="w-4 h-4 mr-2 text-purple-500" />Google AI API</span>
                          <Badge className={systemStatus.google_api === 'configured' ? 'bg-green-100 text-green-800' : systemStatus.google_api === 'not_configured' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}>
                            {systemStatus.google_api || 'Unknown'}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="flex items-center"><Newspaper className="w-4 h-4 mr-2 text-orange-500" />News API Scraper</span>
                          <Badge className={systemStatus.news_api === 'configured' ? 'bg-green-100 text-green-800' : systemStatus.news_api === 'not_configured' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}>
                            {systemStatus.news_api || 'Unknown'}
                          </Badge>
                        </div>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
