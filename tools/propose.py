#!/usr/bin/env python3
"""
Lightweight proposal tracker for multi-instance coordination.

Philosophy: Coordinate on WHAT (proposals, claims, status) to prevent waste.
            Diverge on HOW (execution, thinking) to preserve cognitive diversity.

Usage:
    ./propose.py list                          # View all proposals
    ./propose.py create "question" "desc"      # Create new proposal
    ./propose.py claim <id> <instance>         # Claim a proposal
    ./propose.py status <id> <status>          # Update status
    ./propose.py respond <id> "message"        # Add response to proposal
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROPOSALS_FILE = Path("/bob/.proposals.json")

def load_proposals():
    """Load existing proposals or return empty structure."""
    if not PROPOSALS_FILE.exists():
        return {"proposals": []}
    with open(PROPOSALS_FILE) as f:
        return json.load(f)

def save_proposals(data):
    """Save proposals to file."""
    with open(PROPOSALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def list_proposals():
    """List all proposals with their status."""
    data = load_proposals()
    if not data['proposals']:
        print("No proposals yet.")
        return

    print("\n=== ACTIVE PROPOSALS ===\n")
    for p in data['proposals']:
        status_icon = {
            'open': '○',
            'claimed': '◐',
            'active': '●',
            'complete': '✓'
        }.get(p['status'], '?')

        print(f"{status_icon} [{p['id']}] {p['question']}")
        print(f"   Status: {p['status']}")
        if p.get('claimed_by'):
            print(f"   Claimed by: {', '.join(p['claimed_by'])}")
        if p.get('description'):
            print(f"   Description: {p['description']}")
        if p.get('responses'):
            print(f"   Responses: {len(p['responses'])}")
        print()

def create_proposal(question, description=""):
    """Create a new proposal."""
    data = load_proposals()

    # Generate ID
    proposal_id = f"prop_{len(data['proposals']) + 1:03d}"

    proposal = {
        "id": proposal_id,
        "question": question,
        "description": description,
        "status": "open",
        "created_at": datetime.utcnow().isoformat(),
        "claimed_by": [],
        "responses": []
    }

    data['proposals'].append(proposal)
    save_proposals(data)

    print(f"✓ Created proposal {proposal_id}: {question}")
    return proposal_id

def claim_proposal(proposal_id, instance_id):
    """Claim a proposal (multiple instances can claim same proposal)."""
    data = load_proposals()

    for p in data['proposals']:
        if p['id'] == proposal_id:
            if instance_id not in p['claimed_by']:
                p['claimed_by'].append(instance_id)
                if p['status'] == 'open':
                    p['status'] = 'claimed'
            save_proposals(data)
            print(f"✓ {instance_id} claimed {proposal_id}")
            return

    print(f"✗ Proposal {proposal_id} not found")

def update_status(proposal_id, status):
    """Update proposal status."""
    valid_statuses = ['open', 'claimed', 'active', 'complete']
    if status not in valid_statuses:
        print(f"✗ Invalid status. Use: {', '.join(valid_statuses)}")
        return

    data = load_proposals()
    for p in data['proposals']:
        if p['id'] == proposal_id:
            p['status'] = status
            save_proposals(data)
            print(f"✓ {proposal_id} status → {status}")
            return

    print(f"✗ Proposal {proposal_id} not found")

def add_response(proposal_id, message):
    """Add a response to a proposal."""
    data = load_proposals()

    for p in data['proposals']:
        if p['id'] == proposal_id:
            response = {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message
            }
            p['responses'].append(response)
            save_proposals(data)
            print(f"✓ Added response to {proposal_id}")
            return

    print(f"✗ Proposal {proposal_id} not found")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == 'list':
        list_proposals()
    elif command == 'create':
        if len(sys.argv) < 3:
            print("Usage: propose.py create <question> [description]")
            return
        question = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""
        create_proposal(question, description)
    elif command == 'claim':
        if len(sys.argv) < 4:
            print("Usage: propose.py claim <id> <instance_id>")
            return
        claim_proposal(sys.argv[2], sys.argv[3])
    elif command == 'status':
        if len(sys.argv) < 4:
            print("Usage: propose.py status <id> <status>")
            return
        update_status(sys.argv[2], sys.argv[3])
    elif command == 'respond':
        if len(sys.argv) < 4:
            print("Usage: propose.py respond <id> <message>")
            return
        add_response(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == '__main__':
    main()
