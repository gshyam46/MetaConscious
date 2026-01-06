'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Plus, 
  Clock, 
  Calendar, 
  AlertCircle, 
  CheckCircle2, 
  Circle, 
  Trash2,
  Edit,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';
import { apiRequest } from '@/lib/api-config';

export function TodoList() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [expandedTodos, setExpandedTodos] = useState(new Set());

  useEffect(() => {
    loadTodos();
  }, []);

  const loadTodos = async () => {
    try {
      const response = await apiRequest('/api/todos?status=pending');
      if (response.ok) {
        const data = await response.json();
        setTodos(data);
      }
    } catch (error) {
      console.error('Failed to load todos:', error);
      toast.error('Failed to load todos');
    } finally {
      setLoading(false);
    }
  };

  const createTodo = async (todoData) => {
    try {
      const response = await apiRequest('/api/todos', {
        method: 'POST',
        body: JSON.stringify(todoData)
      });

      if (response.ok) {
        const newTodo = await response.json();
        setTodos(prev => [newTodo, ...prev]);
        toast.success('Todo created');
        setIsCreateDialogOpen(false);
      } else {
        throw new Error('Failed to create todo');
      }
    } catch (error) {
      console.error('Failed to create todo:', error);
      toast.error('Failed to create todo');
    }
  };

  const updateTodoStatus = async (todoId, status) => {
    try {
      const response = await apiRequest(`/api/todos/${todoId}`, {
        method: 'PUT',
        body: JSON.stringify({ status })
      });

      if (response.ok) {
        const updatedTodo = await response.json();
        setTodos(prev => prev.map(todo => 
          todo.id === todoId ? updatedTodo : todo
        ));
        toast.success(`Todo ${status === 'completed' ? 'completed' : 'updated'}`);
      }
    } catch (error) {
      console.error('Failed to update todo:', error);
      toast.error('Failed to update todo');
    }
  };

  const deleteTodo = async (todoId) => {
    try {
      const response = await apiRequest(`/api/todos/${todoId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setTodos(prev => prev.filter(todo => todo.id !== todoId));
        toast.success('Todo deleted');
      }
    } catch (error) {
      console.error('Failed to delete todo:', error);
      toast.error('Failed to delete todo');
    }
  };

  const toggleExpanded = (todoId) => {
    setExpandedTodos(prev => {
      const newSet = new Set(prev);
      if (newSet.has(todoId)) {
        newSet.delete(todoId);
      } else {
        newSet.add(todoId);
      }
      return newSet;
    });
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 5: return 'bg-red-500';
      case 4: return 'bg-orange-500';
      case 3: return 'bg-yellow-500';
      case 2: return 'bg-blue-500';
      case 1: return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getDifficultyLabel = (difficulty) => {
    switch (difficulty) {
      case 1: return 'Easy';
      case 2: return 'Simple';
      case 3: return 'Medium';
      case 4: return 'Hard';
      case 5: return 'Very Hard';
      default: return 'Unknown';
    }
  };

  const formatDuration = (minutes) => {
    if (!minutes) return null;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins > 0 ? `${mins}m` : ''}`;
    }
    return `${mins}m`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Todo List</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground mt-2">Loading todos...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Todo List ({todos.length})</CardTitle>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Todo
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Create New Todo</DialogTitle>
              </DialogHeader>
              <TodoForm onSubmit={createTodo} />
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {todos.length === 0 ? (
          <div className="text-center py-8">
            <Circle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No todos yet. Create your first one!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todos.map((todo) => (
              <div key={todo.id} className="border rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => updateTodoStatus(todo.id, 'completed')}
                    className="p-0 h-6 w-6 text-green-600 hover:text-green-700"
                    title="Mark as completed"
                  >
                    <Circle className="h-4 w-4" />
                  </Button>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-medium truncate">{todo.title}</h4>
                      <Badge variant="outline" className={`${getPriorityColor(todo.priority)} text-white text-xs`}>
                        P{todo.priority}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {getDifficultyLabel(todo.difficulty)}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-muted-foreground mb-2">
                      {todo.estimated_duration && (
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDuration(todo.estimated_duration)}
                        </div>
                      )}
                      {todo.due_date && (
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(todo.due_date)}
                        </div>
                      )}
                    </div>
                    
                    <p className="text-sm text-muted-foreground italic mb-2">
                      {todo.reasoning}
                    </p>
                    
                    {todo.subtasks && todo.subtasks.length > 0 && (
                      <div className="mt-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleExpanded(todo.id)}
                          className="p-0 h-auto text-xs text-muted-foreground"
                        >
                          {expandedTodos.has(todo.id) ? (
                            <ChevronDown className="h-3 w-3 mr-1" />
                          ) : (
                            <ChevronRight className="h-3 w-3 mr-1" />
                          )}
                          {todo.subtasks.length} subtasks
                        </Button>
                        
                        {expandedTodos.has(todo.id) && (
                          <ul className="mt-2 ml-4 space-y-1">
                            {todo.subtasks.map((subtask, index) => (
                              <li key={index} className="text-xs text-muted-foreground flex items-center gap-2">
                                <Circle className="h-2 w-2" />
                                {subtask}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => updateTodoStatus(todo.id, 'completed')}
                      className="p-1 h-6 w-6 text-green-600 hover:text-green-700"
                      title="Mark as completed"
                    >
                      <CheckCircle2 className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => updateTodoStatus(todo.id, 'cancelled')}
                      className="p-1 h-6 w-6 text-orange-600 hover:text-orange-700"
                      title="Cancel/Skip this task"
                    >
                      <AlertCircle className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteTodo(todo.id)}
                      className="p-1 h-6 w-6 text-destructive hover:text-destructive"
                      title="Delete permanently"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TodoForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 3,
    difficulty: 3,
    estimated_duration: '',
    due_date: '',
    reasoning: '',
    subtasks: []
  });
  const [subtaskInput, setSubtaskInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const todoData = {
      ...formData,
      estimated_duration: formData.estimated_duration ? parseInt(formData.estimated_duration) : null,
      due_date: formData.due_date || null
    };
    
    onSubmit(todoData);
    
    // Reset form
    setFormData({
      title: '',
      description: '',
      priority: 3,
      difficulty: 3,
      estimated_duration: '',
      due_date: '',
      reasoning: '',
      subtasks: []
    });
    setSubtaskInput('');
  };

  const addSubtask = () => {
    if (subtaskInput.trim()) {
      setFormData(prev => ({
        ...prev,
        subtasks: [...prev.subtasks, subtaskInput.trim()]
      }));
      setSubtaskInput('');
    }
  };

  const removeSubtask = (index) => {
    setFormData(prev => ({
      ...prev,
      subtasks: prev.subtasks.filter((_, i) => i !== index)
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="title">Title</Label>
        <Input
          id="title"
          value={formData.title}
          onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
          required
        />
      </div>
      
      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          rows={2}
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="priority">Priority (1-5)</Label>
          <Select value={formData.priority.toString()} onValueChange={(value) => setFormData(prev => ({ ...prev, priority: parseInt(value) }))}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1 - Low</SelectItem>
              <SelectItem value="2">2 - Below Normal</SelectItem>
              <SelectItem value="3">3 - Normal</SelectItem>
              <SelectItem value="4">4 - High</SelectItem>
              <SelectItem value="5">5 - Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label htmlFor="difficulty">Difficulty (1-5)</Label>
          <Select value={formData.difficulty.toString()} onValueChange={(value) => setFormData(prev => ({ ...prev, difficulty: parseInt(value) }))}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1 - Easy</SelectItem>
              <SelectItem value="2">2 - Simple</SelectItem>
              <SelectItem value="3">3 - Medium</SelectItem>
              <SelectItem value="4">4 - Hard</SelectItem>
              <SelectItem value="5">5 - Very Hard</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="duration">Duration (minutes)</Label>
          <Input
            id="duration"
            type="number"
            min="5"
            value={formData.estimated_duration}
            onChange={(e) => setFormData(prev => ({ ...prev, estimated_duration: e.target.value }))}
          />
        </div>
        
        <div>
          <Label htmlFor="due_date">Due Date</Label>
          <Input
            id="due_date"
            type="datetime-local"
            value={formData.due_date}
            onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
          />
        </div>
      </div>
      
      <div>
        <Label htmlFor="reasoning">Priority Reasoning</Label>
        <Textarea
          id="reasoning"
          value={formData.reasoning}
          onChange={(e) => setFormData(prev => ({ ...prev, reasoning: e.target.value }))}
          placeholder="Why is this priority justified?"
          required
          rows={2}
        />
      </div>
      
      <div>
        <Label>Subtasks</Label>
        <div className="flex gap-2 mt-1">
          <Input
            value={subtaskInput}
            onChange={(e) => setSubtaskInput(e.target.value)}
            placeholder="Add a subtask..."
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSubtask())}
          />
          <Button type="button" onClick={addSubtask} size="sm">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        {formData.subtasks.length > 0 && (
          <ul className="mt-2 space-y-1">
            {formData.subtasks.map((subtask, index) => (
              <li key={index} className="flex items-center justify-between text-sm bg-muted p-2 rounded">
                <span>{subtask}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeSubtask(index)}
                  className="p-1 h-6 w-6"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <Button type="submit" className="w-full">
        Create Todo
      </Button>
    </form>
  );
}