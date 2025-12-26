'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, Calendar, Target, CheckCircle2, Clock, Users, TrendingUp, Zap } from 'lucide-react';
import { toast } from 'sonner';
import { apiRequest } from '@/lib/api-config';

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [goals, setGoals] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [plan, setPlan] = useState(null);
  const [relationships, setRelationships] = useState([]);
  const [overrideStatus, setOverrideStatus] = useState(null);
  const [llmConfigured, setLlmConfigured] = useState(false);
  const [activeView, setActiveView] = useState('daily');

  // Initialize user and load data
  useEffect(() => {
    initializeApp();
  }, []);

  async function initializeApp() {
    try {
      // Check status
      const statusRes = await apiRequest('/api/status');
      const statusData = await statusRes.json();
      
      setLlmConfigured(statusData.llm_configured);

      if (!statusData.user) {
        // Initialize user
        const initRes = await apiRequest('/api/init', {
          method: 'POST',
          body: JSON.stringify({ username: 'user', password: 'password' }),
        });
        const initData = await initRes.json();
        setUser(initData.user);
      } else {
        setUser(statusData.user);
      }

      // Load data
      await loadDashboardData();
    } catch (error) {
      console.error('Initialization error:', error);
      toast.error('Failed to initialize application');
    } finally {
      setLoading(false);
    }
  }

  function normalizePlan(dbPlan) {
  if (!dbPlan) return null;

  // If already domain-shaped
  if (dbPlan.time_blocks) return dbPlan;

  // DB-shaped → domain-shaped
  if (dbPlan.plan_json) {
    return {
      ...dbPlan.plan_json,
      reasoning: dbPlan.reasoning,
      date: dbPlan.plan_date,
    };
  }

  return null;
}


  async function loadDashboardData() {
    try {
      const [goalsRes, tasksRes, planRes, relationshipsRes, overridesRes] = await Promise.all([
        apiRequest('/api/goals'),
        apiRequest('/api/tasks?status=pending'),
        apiRequest('/api/plans'),
        apiRequest('/api/relationships'),
        apiRequest('/api/overrides'),
      ]);

      const [goalsData, tasksData, planData, relationshipsData, overridesData] = await Promise.all([
        goalsRes.json(),
        tasksRes.json(),
        planRes.json(),
        relationshipsRes.json(),
        overridesRes.json(),
      ]);

      setGoals(goalsData.goals || []);
      setTasks(tasksData.tasks || []);
      setPlan(normalizePlan(planData.plan));
      setRelationships(relationshipsData.relationships || []);
      setOverrideStatus(overridesData.overrides);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  }

  async function createGoal(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    try {
      const res = await apiRequest('/api/goals', {
        method: 'POST',
        body: JSON.stringify({
          title: formData.get('title'),
          description: formData.get('description'),
          priority: parseInt(formData.get('priority')),
          priority_reasoning: formData.get('priority_reasoning'),
          target_date: formData.get('target_date'),
        }),
      });
      
      if (res.ok) {
        toast.success('Goal created');
        e.target.reset();
        loadDashboardData();
      }
    } catch (error) {
      toast.error('Failed to create goal');
    }
  }

  async function createTask(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    try {
      const res = await apiRequest('/api/tasks', {
        method: 'POST',
        body: JSON.stringify({
          title: formData.get('title'),
          description: formData.get('description'),
          priority: parseInt(formData.get('priority')),
          priority_reasoning: formData.get('priority_reasoning'),
          estimated_duration: parseInt(formData.get('estimated_duration')),
          due_date: formData.get('due_date'),
        }),
      });
      
      if (res.ok) {
        toast.success('Task created');
        e.target.reset();
        loadDashboardData();
      }
    } catch (error) {
      toast.error('Failed to create task');
    }
  }

  async function generatePlan() {
    if (!llmConfigured) {
      toast.error('LLM not configured. Set LLM_API_KEY in .env file and restart server.');
      return;
    }

    setLoading(true);
    try {
      const res = await apiRequest('/api/generate-plan', {
        method: 'POST',
        body: JSON.stringify({ date: new Date().toISOString().split('T')[0] }),
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success('Plan generated successfully');
        await loadDashboardData();
      } else {
        toast.error(data.error || 'Failed to generate plan');
      }
    } catch (error) {
      toast.error('Failed to generate plan');
    } finally {
      setLoading(false);
    }
  }

  async function markTaskComplete(taskId) {
    try {
      const res = await apiRequest(`/api/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify({ status: 'completed' }),
      });
      
      if (res.ok) {
        toast.success('Task completed');
        loadDashboardData();
      }
    } catch (error) {
      toast.error('Failed to update task');
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Initializing MetaConscious...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">MetaConscious</h1>
              <p className="text-sm text-muted-foreground">Autonomous AI Planning System v0</p>
            </div>
            <div className="flex items-center gap-4">
              {user && (
                <Badge variant="outline">
                  <Users className="h-3 w-3 mr-1" />
                  {user.username}
                </Badge>
              )}
              {!llmConfigured && (
                <Badge variant="destructive">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  LLM Not Configured
                </Badge>
              )}
              {overrideStatus && (
                <Badge variant={overrideStatus.remaining > 0 ? 'secondary' : 'destructive'}>
                  Overrides: {overrideStatus.remaining}/{overrideStatus.limit}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeView} onValueChange={setActiveView}>
          <TabsList className="mb-6">
            <TabsTrigger value="daily">
              <Calendar className="h-4 w-4 mr-2" />
              Today's Plan
            </TabsTrigger>
            <TabsTrigger value="goals">
              <Target className="h-4 w-4 mr-2" />
              Goals
            </TabsTrigger>
            <TabsTrigger value="tasks">
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Tasks
            </TabsTrigger>
            <TabsTrigger value="social">
              <Users className="h-4 w-4 mr-2" />
              Social
            </TabsTrigger>
          </TabsList>

          {/* Daily Plan View */}
          <TabsContent value="daily" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Today's Plan</CardTitle>
                    <CardDescription>
                      {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </CardDescription>
                  </div>
                  <Button onClick={generatePlan} disabled={!llmConfigured || loading}>
                    <Zap className="h-4 w-4 mr-2" />
                    {plan ? 'Regenerate Plan' : 'Generate Plan'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {!llmConfigured ? (
                  <div className="text-center py-8 space-y-4">
                    <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground" />
                    <div>
                      <p className="font-semibold text-foreground">LLM Not Configured</p>
                      
                    </div>
                  </div>
                ) : !plan ? (
                  <div className="text-center py-8">
                    <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No plan generated yet. Click "Generate Plan" to create today's schedule.</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Plan Reasoning */}
                    <div>
                      <h3 className="font-semibold mb-2 text-foreground">System Analysis</h3>
                      <p className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                        {plan.reasoning}
                      </p>
                    </div>

                    <Separator />

                    {/* Priority Analysis */}
                    <div>
                      <h3 className="font-semibold mb-2 text-foreground">Priority Assessment</h3>
                      <p className="text-sm text-muted-foreground">
                        {plan.priority_analysis || 'No priority analysis available'}
                      </p>
                    </div>

                    <Separator />

                    {/* Time Blocks */}
                    <div>
                      <h3 className="font-semibold mb-3 text-foreground">Schedule</h3>
                      <div className="space-y-2">
                        {plan.time_blocks?.map((block, idx) => (
                          <div key={idx} className="flex items-start gap-4 p-3 bg-muted rounded-md">
                            <div className="text-sm font-mono text-muted-foreground min-w-[100px]">
                              {block.start_time} - {block.end_time}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <p className="font-medium text-foreground">{block.activity}</p>
                                <Badge variant="outline" className="text-xs">
                                  P{block.priority}
                                </Badge>
                              </div>
                              <p className="text-xs text-muted-foreground mt-1">{block.reasoning}</p>
                            </div>
                          </div>
                        )) || <p className="text-sm text-muted-foreground">No schedule blocks</p>}
                      </div>
                    </div>

                    <Separator />

                    {/* Warnings */}
                    {plan.warnings && plan.warnings.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2 text-foreground flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 text-destructive" />
                          System Warnings
                        </h3>
                        <ul className="space-y-1">
                          {plan.warnings.map((warning, idx) => (
                            <li key={idx} className="text-sm text-destructive">
                              • {warning}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Goals View */}
          <TabsContent value="goals" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Goals List */}
              <Card>
                <CardHeader>
                  <CardTitle>Active Goals ({goals.length}/5)</CardTitle>
                  <CardDescription>Long-term objectives with priority reasoning</CardDescription>
                </CardHeader>
                <CardContent>
                  {goals.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">No active goals. Create your first goal.</p>
                  ) : (
                    <div className="space-y-3">
                      {goals.map((goal) => (
                        <div key={goal.id} className="p-3 bg-muted rounded-md">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <p className="font-semibold text-foreground">{goal.title}</p>
                                <Badge variant="outline">P{goal.priority}</Badge>
                              </div>
                              <p className="text-xs text-muted-foreground mb-2">{goal.description}</p>
                              <p className="text-xs text-muted-foreground italic">
                                Reasoning: {goal.priority_reasoning}
                              </p>
                              {goal.target_date && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Target: {new Date(goal.target_date).toLocaleDateString()}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Create Goal Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Create Goal</CardTitle>
                  <CardDescription>Add a new long-term objective</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={createGoal} className="space-y-4">
                    <div>
                      <Label htmlFor="goal-title">Title</Label>
                      <Input id="goal-title" name="title" required />
                    </div>
                    <div>
                      <Label htmlFor="goal-description">Description</Label>
                      <Textarea id="goal-description" name="description" rows={2} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="goal-priority">Priority (1-5)</Label>
                        <Input id="goal-priority" name="priority" type="number" min="1" max="5" defaultValue="3" required />
                      </div>
                      <div>
                        <Label htmlFor="goal-target">Target Date</Label>
                        <Input id="goal-target" name="target_date" type="date" />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="goal-reasoning">Priority Reasoning</Label>
                      <Textarea id="goal-reasoning" name="priority_reasoning" rows={2} placeholder="Why is this priority justified?" required />
                    </div>
                    <Button type="submit" className="w-full">Create Goal</Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Tasks View */}
          <TabsContent value="tasks" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Tasks List */}
              <Card>
                <CardHeader>
                  <CardTitle>Pending Tasks ({tasks.length})</CardTitle>
                  <CardDescription>Tasks awaiting scheduling</CardDescription>
                </CardHeader>
                <CardContent>
                  {tasks.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">No pending tasks.</p>
                  ) : (
                    <div className="space-y-3">
                      {tasks.map((task) => (
                        <div key={task.id} className="p-3 bg-muted rounded-md">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <p className="font-semibold text-foreground">{task.title}</p>
                                <Badge variant="outline">P{task.priority}</Badge>
                              </div>
                              {task.description && (
                                <p className="text-xs text-muted-foreground mb-2">{task.description}</p>
                              )}
                              <p className="text-xs text-muted-foreground italic">
                                Reasoning: {task.priority_reasoning}
                              </p>
                              <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                                {task.estimated_duration && (
                                  <span className="flex items-center gap-1">
                                    <Clock className="h-3 w-3" />
                                    {task.estimated_duration}min
                                  </span>
                                )}
                                {task.due_date && (
                                  <span>
                                    Due: {new Date(task.due_date).toLocaleDateString()}
                                  </span>
                                )}
                              </div>
                            </div>
                            <Button size="sm" variant="ghost" onClick={() => markTaskComplete(task.id)}>
                              <CheckCircle2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Create Task Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Create Task</CardTitle>
                  <CardDescription>Add a new task to be scheduled</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={createTask} className="space-y-4">
                    <div>
                      <Label htmlFor="task-title">Title</Label>
                      <Input id="task-title" name="title" required />
                    </div>
                    <div>
                      <Label htmlFor="task-description">Description</Label>
                      <Textarea id="task-description" name="description" rows={2} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="task-priority">Priority (1-5)</Label>
                        <Input id="task-priority" name="priority" type="number" min="1" max="5" defaultValue="3" required />
                      </div>
                      <div>
                        <Label htmlFor="task-duration">Duration (min)</Label>
                        <Input id="task-duration" name="estimated_duration" type="number" min="5" />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="task-due">Due Date</Label>
                      <Input id="task-due" name="due_date" type="date" />
                    </div>
                    <div>
                      <Label htmlFor="task-reasoning">Priority Reasoning</Label>
                      <Textarea id="task-reasoning" name="priority_reasoning" rows={2} placeholder="Why is this priority justified?" required />
                    </div>
                    <Button type="submit" className="w-full">Create Task</Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Social View */}
          <TabsContent value="social" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Social Time Management</CardTitle>
                <CardDescription>Relationships with time budgets and tracking</CardDescription>
              </CardHeader>
              <CardContent>
                {relationships.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No relationships tracked. Social time module is scaffolded.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {relationships.map((rel) => (
                      <div key={rel.id} className="p-3 bg-muted rounded-md">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-foreground">{rel.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {rel.relationship_type} • P{rel.priority}
                            </p>
                          </div>
                          <Badge variant="outline">
                            {rel.time_budget_hours}h/week
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t mt-12 py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>MetaConscious v0 • Autonomous AI Planning System</p>
          <p className="mt-2">System has FINAL AUTHORITY over scheduling • Override limit enforced</p>
        </div>
      </footer>
    </div>
  );
}