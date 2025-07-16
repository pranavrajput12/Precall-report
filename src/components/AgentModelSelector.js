import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const fetchModels = async () => {
  const res = await fetch('/api/config/models');
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
};

const assignModel = async ({ agentId, modelId }) => {
  const res = await fetch(`/api/config/agents/${agentId}/model?model_id=${modelId}`, { method: 'PUT' });
  if (!res.ok) throw new Error('Failed to assign model');
  return res.json();
};

export default function AgentModelSelector({ agent, onChange }) {
  const queryClient = useQueryClient();
  const { data: models = [], isLoading } = useQuery({ queryKey: ['models'], queryFn: fetchModels });
  const mutation = useMutation({
    mutationFn: assignModel,
    onSuccess: () => {
      toast.success('Model updated!');
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      if (onChange) onChange();
    },
    onError: (e) => toast.error(e.message),
  });

  const handleChange = (e) => {
    const modelId = e.target.value;
    mutation.mutate({ agentId: agent.id, modelId });
  };

  return (
    <div className="agent-model-selector">
      <label>Model:</label>
      <select value={agent.model_id || ''} onChange={handleChange} disabled={isLoading || mutation.isLoading}>
        <option value="">(Select a model)</option>
        {models.map((m) => (
          <option key={m.id} value={m.id}>{m.name} ({m.config?.deployment_name})</option>
        ))}
      </select>
    </div>
  );
} 