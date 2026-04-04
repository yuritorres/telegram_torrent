import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FileGrid } from '../FileGrid';

// Mock react-use-measure
vi.mock('react-use-measure', () => ({
    default: () => [() => { }, { width: 800, height: 600 }]
}));

// Mock i18next
vi.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key) => key,
    }),
}));

// Mock useClipboard
vi.mock('../../../context/ClipboardContext', () => ({
    useClipboard: () => ({
        copy: new Set(),
        cut: new Set(),
        clipboard: { items: [], action: null }
    })
}));

// Mock useDragSelection
vi.mock('../../../hooks/useDragSelection', () => ({
    useDragSelection: () => ({
        isSelecting: false,
        selectionBox: null,
        containerRef: { current: null },
        handleMouseDown: vi.fn()
    })
}));

// Mock react-window
vi.mock('react-window', () => {
    const Grid = ({ cellComponent: Child, cellProps, ...props }) => (
        <div data-testid="grid-mock">
            {/* Simulate a few items */}
            <Child columnIndex={0} rowIndex={0} style={{}} data={cellProps.data} />
        </div>
    );
    const List = ({ rowComponent: Child, rowProps, ...props }) => (
        <div data-testid="list-mock">
            <Child index={0} style={{}} data={rowProps.data} />
        </div>
    );
    return {
        Grid,
        List,
        default: {
            Grid,
            List
        }
    };
});

describe('FileGrid', () => {
    const mockFiles = [
        { id: '1', name: 'test.txt', type: 'file', size: '1KB', date: '2023-01-01' }
    ];

    it('renders the grid view by default', () => {
        render(
            <FileGrid
                files={mockFiles}
                viewMode="grid"
                selectedFileIds={[]}
                onSelect={() => { }}
                onNavigate={() => { }}
                onContextMenu={() => { }}
                sortConfig={{}}
                requestSort={() => { }}
            />
        );
        expect(screen.getByText('test.txt')).toBeInTheDocument();
    });

    it('renders in list mode', () => {
        render(
            <FileGrid
                files={mockFiles}
                viewMode="list"
                selectedFileIds={[]}
                onSelect={() => { }}
                onNavigate={() => { }}
                onContextMenu={() => { }}
                sortConfig={{}}
                requestSort={() => { }}
            />
        );
        expect(screen.getByTestId('list-mock')).toBeInTheDocument();
    });

    it('displays empty state', () => {
        render(
            <FileGrid
                files={[]}
                viewMode="grid"
                selectedFileIds={[]}
                onSelect={() => { }}
                onNavigate={() => { }}
                onContextMenu={() => { }}
                sortConfig={{}}
                requestSort={() => { }}
            />
        );
        expect(screen.getByText('grid.emptyTitle')).toBeInTheDocument();
    });
});
