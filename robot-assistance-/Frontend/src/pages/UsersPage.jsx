import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";
import { fmtDate } from "../utils/date";

export default function UsersPage({
  users,
  userForm,
  onUserFormChange,
  onSubmitUser,
  userEditId,
  userEditForm,
  onUserEditFormChange,
  onSubmitUserUpdate,
  onStartUserEdit,
  onCancelUserEdit,
  onDeactivateUser,
  onActivateUser,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Create User" subtitle="POST /api/users">
        <form className="form-grid" onSubmit={onSubmitUser}>
          <input
            required
            placeholder="Full name"
            value={userForm.name}
            onChange={(event) => onUserFormChange("name", event.target.value)}
          />
          <input
            required
            type="email"
            placeholder="Email"
            value={userForm.email}
            onChange={(event) => onUserFormChange("email", event.target.value)}
          />
          <input
            required
            type="password"
            placeholder="Password (min 8)"
            value={userForm.password}
            onChange={(event) => onUserFormChange("password", event.target.value)}
          />
          <select
            value={userForm.role}
            onChange={(event) => onUserFormChange("role", event.target.value)}
          >
            <option value="employee">Employee</option>
            <option value="admin">Admin</option>
            <option value="visitor">Visitor</option>
            <option value="executive">Executive</option>
          </select>
          <input
            placeholder="Department"
            value={userForm.department}
            onChange={(event) => onUserFormChange("department", event.target.value)}
          />
          <input
            placeholder="Preferred language"
            value={userForm.preferred_language}
            onChange={(event) => onUserFormChange("preferred_language", event.target.value)}
          />
          <button className="btn btn-primary" type="submit">
            Create User
          </button>
        </form>
      </Panel>

      {userEditId ? (
        <Panel title={`Update User #${userEditId}`} subtitle="PUT /api/users/{user_id}">
          <form className="form-grid" onSubmit={onSubmitUserUpdate}>
            <input
              required
              placeholder="Full name"
              value={userEditForm.name}
              onChange={(event) => onUserEditFormChange("name", event.target.value)}
            />
            <input
              required
              type="email"
              placeholder="Email"
              value={userEditForm.email}
              onChange={(event) => onUserEditFormChange("email", event.target.value)}
            />
            <input
              type="password"
              placeholder="New password (optional)"
              value={userEditForm.password}
              onChange={(event) => onUserEditFormChange("password", event.target.value)}
            />
            <select
              value={userEditForm.role}
              onChange={(event) => onUserEditFormChange("role", event.target.value)}
            >
              <option value="employee">Employee</option>
              <option value="admin">Admin</option>
              <option value="visitor">Visitor</option>
              <option value="executive">Executive</option>
            </select>
            <input
              placeholder="Department"
              value={userEditForm.department}
              onChange={(event) => onUserEditFormChange("department", event.target.value)}
            />
            <input
              placeholder="Preferred language"
              value={userEditForm.preferred_language}
              onChange={(event) => onUserEditFormChange("preferred_language", event.target.value)}
            />
            <select
              value={userEditForm.is_active ? "active" : "inactive"}
              onChange={(event) => onUserEditFormChange("is_active", event.target.value === "active")}
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <div className="row-actions">
              <button className="btn btn-primary" type="submit">
                Save User
              </button>
              <button className="btn btn-muted" type="button" onClick={onCancelUserEdit}>
                Cancel
              </button>
            </div>
          </form>
        </Panel>
      ) : null}

      <Panel title="Users" subtitle="GET /api/users and DELETE /api/users/{user_id}">
        <div className="list-wrap">
          {users.length === 0 ? (
            <EmptyState title="No users found" detail="Create a user from the panel above." />
          ) : (
            users.map((user) => (
              <article className="list-item" key={`user-${user.id}`}>
                <h3>
                  {user.name} (#{user.id})
                </h3>
                <p>
                  {user.email} | Role: {user.role}
                </p>
                <p>
                  Department: {user.department || "N/A"} | Language: {user.preferred_language || "en"}
                </p>
                <p>
                  Status: {user.is_active ? "active" : "inactive"} | Updated: {fmtDate(user.updated_at)}
                </p>
                <div className="row-actions">
                  <button className="btn btn-muted" type="button" onClick={() => onStartUserEdit(user)}>
                    Edit
                  </button>
                  {user.is_active ? (
                    <button className="btn btn-danger" type="button" onClick={() => onDeactivateUser(user.id)}>
                      Deactivate
                    </button>
                  ) : (
                    <button className="btn btn-primary" type="button" onClick={() => onActivateUser(user.id)}>
                      Activate
                    </button>
                  )}
                </div>
              </article>
            ))
          )}
        </div>
      </Panel>
    </main>
  );
}
