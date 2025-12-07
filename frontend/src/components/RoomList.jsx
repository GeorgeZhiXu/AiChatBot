import { useState } from 'react';

/**
 * Room List Sidebar Component
 */
export function RoomList({ rooms, currentRoom, onRoomSwitch, onCreateRoom, onDeleteRoom }) {
  const [showCreateModal, setShowCreateModal] = useState(false);

  return (
    <div className="room-list">
      <div className="room-list-header">
        <h3>Chat Rooms</h3>
        <button
          className="create-room-btn"
          onClick={() => setShowCreateModal(true)}
          title="Create new room"
        >
          +
        </button>
      </div>

      <div className="room-list-body">
        {rooms.length === 0 ? (
          <div className="empty-rooms">No rooms available</div>
        ) : (
          rooms.map(room => (
            <div
              key={room.id}
              className={`room-item ${currentRoom?.id === room.id ? 'active' : ''}`}
              onClick={() => onRoomSwitch(room)}
            >
              <div className="room-info">
                <div className="room-name">
                  {room.is_private && '🔒 '}
                  {room.name}
                </div>
                {room.description && (
                  <div className="room-description">{room.description}</div>
                )}
              </div>
              {currentRoom?.id === room.id && room.name !== 'General' && (
                <button
                  className="delete-room-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm(`Delete room "${room.name}"?`)) {
                      onDeleteRoom(room.id);
                    }
                  }}
                  title="Delete room"
                >
                  🗑️
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {showCreateModal && (
        <CreateRoomModal
          onClose={() => setShowCreateModal(false)}
          onCreate={onCreateRoom}
        />
      )}
    </div>
  );
}

/**
 * Create Room Modal
 */
function CreateRoomModal({ onClose, onCreate }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await onCreate({ name, description, is_private: isPrivate });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create room');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create New Room</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Room Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Project Alpha"
              required
              maxLength={50}
              autoFocus
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              maxLength={200}
              rows={3}
            />
          </div>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={isPrivate}
                onChange={(e) => setIsPrivate(e.target.checked)}
              />
              <span>Private room (invite only)</span>
            </label>
          </div>

          {error && <div className="form-error">⚠️ {error}</div>}

          <div className="modal-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !name.trim()}
            >
              {loading ? 'Creating...' : 'Create Room'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
